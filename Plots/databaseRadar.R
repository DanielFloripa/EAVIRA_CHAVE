#!/usr/bin/env Rscript
###################################################
#### This R script is part of CHAVE-SIM Project####
#### Avalable at dscar.ga/chave                ####
###################################################
#                   1   2   3   4   7   6   7
#                 AZ1 AZ2 AZ3 AZ4 AZ5 AZ6 Global
#1     Place        ?   ?   ?   ?   ?   ?   ?     
#2     Place_HA     ?   ?   ?   ?   ?   ?   ?     
#3     Unlock       ?   ?   ?   ?   ?   ?   ?     
#4     Unlock_HA    ?   ?   ?   ?   ?   ?   ?     
#5     Lock_Rand    ?   ?   ?   ?   ?   ?   ?     
#6     Lock_Rand_HA ?   ?   ?   ?   ?   ?   ?      
#7     Max          ?   ?   ?   ?   ?   ?   ?     
#8     Max_HA       ?   ?   ?   ?   ?   ?   ?     
#9     EUCA         ?   ?   ?   ?   ?   ?   ? 
# matrix_db[[11,1]] or matrix_db[["EUCA","AZ1"]] or matrix_db["EUCA",] or matrix_db[,"AZ1"]
############################## 0.0) LIBRARIES AND PACKAGES ####
# install.packages(c("RSQLite", "ggplot2", "fmsb"),repos = "http://cran.us.r-project.org", quiet=TRUE)
library("fmsb")
library("ggplot2")
library("DBI")
############################## 0.1) MAIN PARAMETERS AND DIRS #################################
# Get the parameter: # date = commandArgs(trailingOnly=TRUE)

path = commandArgs(trailingOnly=TRUE)

if(length(path) == 0 ){
  date = "18.07.21-17.18.46/"
  pwd <- "/home/daniel/output/"
  #pwd <- "/media/debian/"
  #pwd <- "~/Dropbox/UDESC/Mestrado/Pratico/CHAVE-Sim/output/"
  root <- paste0(toString(pwd), toString(date), toString("results/"))
} else{
  root <- paste0(toString(path), toString("results/"))
}


test_l <- c("CHAVE_CF_L:None_O:False_C:False_R:False", "CHAVE_CF_L:None_O:False_C:False_R:True",
            "CHAVE_LOCK_L:False_O:False_C:True_R:False", "CHAVE_LOCK_L:False_O:False_C:True_R:True",
            "CHAVE_LOCK_L:RANDOM_O:False_C:True_R:False", "CHAVE_LOCK_L:RANDOM_O:False_C:True_R:True",
            "CHAVE_MAX_L:None_O:False_C:True_R:False", "CHAVE_MAX_L:None_O:False_C:True_R:True",
            "EUCA_CF_L:None_O:False_C:False_R:False")
tests_names <- c("P", "P_HA", "C_AA0", "CHA_AA0", "C_AA20", "CHA_AA20", "C_MAX", "CHA_MAX", "EUCA")
AZ_names = c("AZ1", "AZ2", "AZ3","AZ4","AZ5","AZ6", "Global")
df_test_name <- data.frame(test_l, tests_names)

############################## 0.2) CHOOSE THE DIRECTORY #####################
out <- tryCatch({
    setwd(root)
    local_tests <- list.files()
    for (i in 1:length(local_tests)){
        if (local_tests[i] != test_l[i]){
            message("ERROR: Files are different!")
            message(local_tests[i])
        }
    }
},
error=function(cond){
    message("ERROR: Maybe you have other files in <dir>")
    message(root)
},
warning=function(cond){
    message("WARNING:")
    message(root)
},
finnaly={
    message("OK! Changing dir to: ")
    print(root)
})
############################## 0.3) CONNECT TABLE AND TEST THE DB_FILES ##################################################
az_con_list <- c()
for (folder in local_tests){
    #message(paste0(toString("Reading: "), toString(folder)))
    files <- list.files(path = folder, pattern="*.db") # , ignore.case = TRUE)
    for(ff in files){
        fdr_file <- paste0(toString(folder), toString("/"), toString(ff))
        #print(fdr_file)
        for(f in ff){
            if(!file.exists(fdr_file)){
                message("ERROR ON: ")
                message(f)
                break
            }
            else {
                az_con_list <- c(az_con_list, dbConnect(RSQLite::SQLite(), fdr_file, synchronous = NULL))
            }
        }
    }
}
matrix_db <- matrix(data=az_con_list, byrow=TRUE, nrow = length(local_tests), 
                    ncol = length(AZ_names), dimnames = list(tests_names, AZ_names))
dbListTables(matrix_db[[1,1]])
dbListTables(matrix_db[["EUCA","AZ6"]])
############################## 0.6) BASIC QUERIES ###############
q_info_str <- "SELECT count(val_0) FROM {} WHERE INSTR(info, 'substring') > 0" # or use the LIKE operator

# h_av: # em percentual de requisições
q_replic_attend = "SELECT count(ai) FROM replic_d"
q_replic_add_host = "SELECT count(ai) FROM replic_d WHERE abs(val_0) > 0"
q_replic_add_energy = "SELECT sum(energy_f - energy_0) FROM replic_d"
# cons: # quantidade de operações realizadas
q_cons = "SELECT count(val_0) FROM consol_d"
q_cons_false_pos = "SELECT count(ai) from consol_d where val_0 = 0"
q_cons_migrations = "SELECT sum(val_f) from consol_d where val_0 > 0"
# energy: # em eficiencia/redução total
q_ener = "SELECT sum(val_0)/1000 FROM energy_l"
q_ener_cons = "SELECT sum(energy_0 - energy_f) FROM consol_d"
q_ener_ha = "SELECT sum(energy_0 - energy_f) FROM replic_d"
# load: # percentual medio de carga
q_avg_load <- 'SELECT avg(val_0)*100 FROM az_load_l'
q_avg_load_max <- 'SELECT max(val_0) FROM az_load_l'
q_avg_load_min <- 'SELECT min(val_0) FROM az_load_l'
q_az_load_val_0 <- 'SELECT val_0 FROM az_load_l'
q_az_load_val_0_gvt <- 'SELECT val_0, gvt FROM az_load_l'
q_energy_load <- 'SELECT val_0 FROM energy_l WHERE gvt=(SELECT gvt FROM az_load_l WHERE val_0 > 0)'
# reject/slav: # quantidade de rejeições
q_reject = "SELECT count(val_0) FROM reject_l"

fun_q_select_from_load<-function(metric, table, load){
    return(paste0("SELECT ", toString(metric), " FROM ", toString(table), 
                  " WHERE gvt=(SELECT gvt FROM az_load_l WHERE val_0<=", 
                  toString(load+ERR)," and val_0>=", toString(load-ERR), ")"))
}

fun_q_join<-function(metric, table, load, erro){
    return(paste0("SELECT ", toString(metric), " FROM ", toString(table), 
                  " as t inner join az_load_l as l on l.gvt=t.gvt and (l.val_0 <= ", 
                  toString(load+erro)," and l.val_0 >= ", toString(load-erro),")"))
}

metric2<-"t.gvt as gvt, t.energy_0, t.energy_f, max(t.energy_0-t.energy_f) as reduc_val, (t.energy_0-t.energy_f)/t.energy_0 as reduc_p, t.val_0 as fals_pos, t.val_f as migrations, l.val_0 as load, t.info as info"

################################ 2.2.0 GENERAL DATA ##############################

load_all <- c(25.320513,  0.000000, 72.435897,
                28.571429, 29.761905, 17.857143,
                0.000000,  1.785714,  3.571429,
                8.333333,  0.000000, 33.333333,
                71.471774, 67.439516, 69.758065,
                64.648438, 64.843750, 66.992188)/100
load_objectives <- c(load_all[1], load_all[4], load_all[9], load_all[10], load_all[13], load_all[16])

###### APENAS PARA consol_d ####

synk_name <- "../Plots/output.txt"
this_tests_names <- c(tests_names[3:8])
AZ_names2 <- AZ_names[1:6]
CREATE_QUERIES = FALSE
if (CREATE_QUERIES == TRUE){
  #load_objectives <- c(load_all[1], load_all[4]) #, load_all[13], load_all[16])
  obj<-1
  sink(synk_name)
  for (az in AZ_names2){ #[1:6]){ 
      if (obj == 1){
        cat("AZ_ERR_CONS<-data.frame(")
        cat("\n")
      }
      cat(paste0(az, "<-matrix(c("))
      cat("\n")
      for(t in this_tests_names){
          ERR<-0.01
          ERR_l <- c()
          for(i in seq(1, 99)){
              qq <- fun_q_join("t.gvt, l.val_0 as load", "consol_d", load_objectives[obj], ERR)
              qq2 <- fun_q_join(metric2, "consol_d", load_objectives[obj], ERR)
              x<-dbGetQuery(matrix_db[[t, az]], qq)
              l<-length(x$load)
              if(l == 0){
                  ERR <- ERR + 0.01
              }
              else {
                  ERR_l <- c(ERR_l, ERR)
                  cat(c("'", t,"'", ", ", l, ", ",  ERR_l, ", ", "'",qq2,"'"), sep = "", append = TRUE)
                  if (t != this_tests_names[length(this_tests_names)]){
                    cat(",\n")
                  }
                  break
              }
          }
      }
      obj<-obj+1
      cat("), ncol=4, byrow = TRUE)", append = TRUE)
      if (az != AZ_names2[length(AZ_names2)]){
        cat(",\n")
      }
  }
  cat(")\n", append = TRUE)
  colnames_s<-c()
  for(az in AZ_names2){
    vv<-","
    if (az == AZ_names2[length(AZ_names2)]){
      vv<-""
    }
    colnames_s<- c(colnames_s, paste0("'", az,".alg',","'", az,".qtd',","'", az,".err',","'", az,".query'",vv))
  }
  ff<-function(vec){
    x=""
    for (e in vec){
      x<-paste0(x,e)
    }
    return(x)
  }
  tests_names[9]
  cat("colnames(AZ_ERR_CONS)=(c(", append = TRUE)
  cat(ff(colnames_s))
  cat("))\n", append = TRUE) #"colnames(AZ_ERR_CONS)=(c('AZ1.alg', 'AZ1.qtd', 'AZ1.err', 'AZ1.query', 'AZ5.alg','AZ5.qtd', 'AZ5.err', 'AZ5.query', 'AZ6.alg', 'AZ6.qtd', 'AZ6.err', 'AZ6.query'))\n", append = TRUE)
  cat("rownames(AZ_ERR_CONS)=this_tests_names\n")
  cat("as.character(AZ_ERR_CONS['CHAVE_MAX','AZ1.err'])\n")
  sink()
  sink()
  source(synk_name, local = TRUE)
}

############################## 2.2.1) SNAPSHOTS RADAR CHARTS ##################
source(synk_name, local = TRUE)
#source("/home/daniel/Dropbox/UDESC/Mestrado/Pratico/CHAVE-Sim/Plots/databaseRadar_sources.R")
#c("P", "P_HA", "C_AA0", "CHA_AA0", "C_AA20", "CHA_AA20", "C_MAX", "CHA_MAX", "EUCA")

print("Executing radar chart:")
this_az<-AZ_names[1:6]
for(az in this_az){
    #az="AZ1"
    print(az)
    fun_g_query <- function(test, query){
        db<-matrix_db[[test, az]]
        resp<-dbGetQuery(db, query)
        return(resp)
    }
    qcol<-paste0(az,".query")
    snapshots<-c()
    snapshots <- c(as.data.frame(mapply(fun_g_query, this_tests_names, as.character(AZ_ERR_CONS[,qcol]))))
    
    load <- sapply(snapshots,'[[',"load")
    reducp <-sapply(snapshots,'[[',"reduc_p")
    energyf <-sapply(snapshots,'[[',"energy_f")
    migration <-sapply(snapshots,'[[',"migrations")
    reduc_val <-sapply(snapshots,'[[',"reduc_val")
    gvt <-sapply(snapshots,'[[',"gvt")
    print(gvt)
    #myEUCA = c()
    #for(i in range(1,length(this_tests_names))){
    #  queryEn = paste0("select val_0 as energy from energy_l where gvt=", gvt[[this_tests_names[i]]])
    #  queryL = paste0("select val_0 as load from az_load_l where gvt=", gvt[[this_tests_names[i]]])
    #  EN_EUCA = fun_g_query("EUCA", queryEn)
    #  L_EUCA = fun_g_query("EUCA", queryL)
    #  myEUCA <- c(myEUCA, EN_EUCA, L_EUCA)
    #}
    
    
    #az1=gvt=1543723, load=%, energy=
    #az2 gvt=10680920, load=1,19%, energy=848.57
    
    
    data <- as.data.frame(matrix( c(load, energyf , migration , reduc_val, reducp), ncol=5))
    ## Metrics:
    #colnames(data)=c("Carga (%)" , "Redução (%)", "Energia Total (W)", "Nº Migrações", "Redução (W)")
    colnames(data)=c("C(%)" , "T(W)", "N(n)", "RE(W)", "RE(%)")
    # Tests:
    rownames(data)=this_tests_names
    ## To use the fmsb package, I have to add 2 lines to the dataframe: the max and min of each topic to show on the plot!
    data=rbind(c(max(load), max(energyf), max(migration), min(reduc_val), min(reducp)), # Max values in range
               c(min(load), min(energyf), min(migration), max(reduc_val), max(reducp)), data)                     # Min values in range
    dput(data)
    #mar is c(bottom, left, top, right)
    par(mar=c(3,4,4,5)+0.1)
    tranp<-1
    colors_border=c( rgb(0.0, 0.0, 1.0, tranp), # blue
                     rgb(0.0, 0.9, 1.0, tranp), # light blue
                     rgb(0.9, 0.0, 0.0, tranp), # red
                     rgb(1.0, 0.7, 0.0, tranp), # orange
                     rgb(0.1, 0.5, 0.1, tranp), # darkgreen
                     rgb(0.3, 0.8, 0.1, tranp), # lightgreen
                     rgb(1.0, 0.2, 0.7, tranp)) # pink
                     #rgb(0.0, 0.9, 0.8, tranp))
    #colors_in=c( rgb(0.0,0.0,0.9,0.3),rgb(0.9,0.0,0.0,0.3),rgb(0.9,0.9,0.0,0.3),rgb(0.0,0.6,0.2,0.3),rgb(0.5,0.2,1.0,0.3),rgb(0.0,0.9,0.8,0.3),rgb(0.7,0.8,0.2,0.3))
    line_type=c(1, 5, 1, 5, 1, 5, 1)
    line_pch=c(21, 22, 21, 22, 21, 22, 33)
    line_pch2=c(19, 15, 19, 15, 19, 15, 17)
    mypdf<-paste0("../radar_", toString(az), ".pdf")
    pdf(mypdf, title=az, width = 12, height = 7)
    radarchart( data, axistype=1, title=paste("Testes ",az),
                #custom polygon
                pcol=colors_border, plwd=5 , plty=line_type, pty=line_pch2, # , pfcol=colors_in 
                #custom the grid
                cglcol="grey", cglty=1, axislabcol="grey", caxislabels=seq(0,100,25), cglwd=1,
                #custom labels
                vlcex=2 
    )
    #legend(x=-0.9, y=-0.9, legend = rownames(data[-c(1,2),]), horiz=TRUE,
    #       y.intersp=2, x.intersp=1, bty="n", pch=line_pch, lty = line_type, lwd = 3,
    #       col=colors_border, text.col = "black", cex=1.2, pt.cex=4) #,title=paste("Testes ",az))
    dev.off()
}



################################ 2.3.0 GENERAL DATA ##############################


q_cons <- "SELECT sum(energy_0-energy_f) as reduc_val, count(ai) as trigger, sum(val_f) as migrations, COUNT(CASE WHEN val_0 = 0 then 1 ELSE NULL END) as fals_pos from consol_d"
q_slav <- "SELECT count(ai) as slav FROM reject_l"
q_energy<-"SELECT sum(val_0) as energy_reduct FROM energy_l"

#jj_12<-"SELECT sum(c.energy_0 - c.energy_f) as reduc_val, count(c.ai) as trigger, sum(c.val_f) as migrations, count(r.ai) as slav, sum(e.val_0) as energy_reduct FROM consol_d as c INNER JOIN energy_l as e JOIN reject_l as r"

synk_name2 <- "../Plots/output_global.txt"
this_tests_names <- c(tests_names[3:8])
AZ_names2 <- AZ_names[1:6]
CREATE_QUERIES = TRUE
if (CREATE_QUERIES == TRUE){
  obj<-1
  sink(synk_name2)
  for (az in AZ_names2){ #[1:6]){ 
    if (az == AZ_names2[1]){
      cat("AZ_METRIC_global<-data.frame(\n")
    }
    cat(paste0(az, "<-matrix(c(\n"))
    for(t in this_tests_names){
      cat(c("'", t,"', ", "'",q_cons,"', ", "'",q_slav,"', ", "'",q_energy,"'"), sep = "", append = TRUE)
      if (t != this_tests_names[length(this_tests_names)]){
        cat(",\n")
      }
    }
    obj<-obj+1
    cat("), ncol=4, byrow = TRUE)", append = TRUE)
    if (az != AZ_names2[length(AZ_names2)]){
      cat(",\n")
    }
  }
  cat(")\n", append = TRUE)
  colnames_s<-c()
  for(az in AZ_names2){
    vv<-","
    if (az == AZ_names2[length(AZ_names2)]){
      vv<-""
    }
    colnames_s<- c(colnames_s, paste0("'", az,".alg',","'", az,".q1',","'", az,".q2',","'", az,".q3'",vv))
  }
  ff<-function(vec){
    x=""
    for (e in vec){
      x<-paste0(x,e)
    }
    return(x)
  }
  cat("colnames(AZ_METRIC_global)=(c(", append = TRUE)
  cat(ff(colnames_s))
  cat("))\n", append = TRUE) 
  cat("rownames(AZ_METRIC_global)=this_tests_names\n")
  cat("as.character(AZ_METRIC_global['CHAVE_MAX','AZ1.q1'])\n")
  sink()
  source(synk_name2, local = TRUE)
}

source(synk_name2, local = TRUE)
############################## 2.3.1) GENERAL RADAR CHARTS ##################

print("Executing (23) radar2:")
for(az in AZ_names[1:6]){
  print(az)
  fun_g_query <- function(test, query){
    db<-matrix_db[[test, az]]
    resp<-dbGetQuery(db, query)
    return(resp)
  }
  qcol1<-paste0(az,".q1")
  qcol2<-paste0(az,".q2")
  qcol3<-paste0(az,".q3")
  snapshots2<-c()
  df21 <- data.frame(mapply(fun_g_query, this_tests_names, as.character(AZ_METRIC_global[,qcol1])))
  df22 <- data.frame(mapply(fun_g_query, this_tests_names, as.character(AZ_METRIC_global[,qcol2])))
  rownames(df22)="slav"
  colnames(df22)=this_tests_names
  df23 <- data.frame(mapply(fun_g_query, this_tests_names, as.character(AZ_METRIC_global[,qcol3])))
  rownames(df23)="energy_cons"
  colnames(df23)=this_tests_names

  dff<-rbind(df21, df22, df23)
  snapshots2<-c(dff)
  
  reduc_val <- sapply(snapshots2,'[[',"reduc_val")
  trigger <- sapply(snapshots2,'[[',"trigger")
  migrations <-sapply(snapshots2,'[[',"migrations")
  fals_pos <-sapply(snapshots2,'[[',"fals_pos")
  slav <-sapply(snapshots2,'[[',5)
  energy_cons <-sapply(snapshots2,'[[',6)/1e6  # Transf to MegaWatts
  
  data <- as.data.frame(matrix( c(reduc_val, trigger, migrations , fals_pos , slav, energy_cons), ncol=6))
  ## Metrics:
  colnames(data)=c("RE(W)", "Tr(n)" , "M(n)", "FP(n)", "SLAV(n)", "T(W)")
  # Tests:
  rownames(data)=this_tests_names
  data=rbind(c(min(reduc_val), max(trigger), max(migrations), max(fals_pos), max(slav), max(energy_cons)), # Max values in range
             c(max(reduc_val), min(trigger), min(migrations), min(fals_pos), min(slav), min(energy_cons)), data) # Min values in range
  #mar is c(bottom, left, top, right)
  par(mar=c(3,4,4,5)+0.1)
  tranp<-1
  colors_border=c( rgb(0.0, 0.0, 1.0, tranp), # blue
                   rgb(0.0, 0.9, 1.0, tranp), # light blue
                   rgb(0.9, 0.0, 0.0, tranp), # red
                   rgb(1.0, 0.7, 0.0, tranp), # orange
                   rgb(0.1, 0.5, 0.1, tranp), # darkgreen
                   rgb(0.3, 0.8, 0.1, tranp), # lightgreen
                   rgb(1.0, 0.2, 0.7, tranp)) # pink
  #rgb(0.0, 0.9, 0.8, tranp))
  #colors_in=c( rgb(0.0,0.0,0.9,0.3),rgb(0.9,0.0,0.0,0.3),rgb(0.9,0.9,0.0,0.3),rgb(0.0,0.6,0.2,0.3),rgb(0.5,0.2,1.0,0.3),rgb(0.0,0.9,0.8,0.3),rgb(0.7,0.8,0.2,0.3))
  line_type=c(1, 5, 1, 5, 1, 5, 1)
  line_pch=c(21, 22, 21, 22, 21, 22, 33)
  line_pch2=c(19, 15, 19, 15, 19, 15, 17)
  mypdf<-paste0("../gen_radar_", toString(az), ".pdf")
  pdf(mypdf, title=az, width = 12, height = 7)
  radarchart( data, axistype=1, title=paste("Testes ",az),
              #custom polygon
              pcol=colors_border, plwd=5 , plty=line_type, pty=line_pch2, # , pfcol=colors_in 
              #custom the grid
              cglcol="grey", cglty=1, axislabcol="grey", caxislabels=seq(0,100,25), cglwd=1,
              #custom labels
              vlcex=2 
  )
  #legend(x=1.5, y=1, legend = rownames(data[-c(1,2),]), # horiz=TRUE,
  #       y.intersp=2, x.intersp=1, bty="n", pch=line_pch, lty = line_type, lwd = 3,
  #       col=colors_border, text.col = "black", cex=1.2, pt.cex=4,title=paste("Testes ",az))
  dev.off()
}

################################ 2.4.0 GENERAL DATA ##############################
synk_name3 <- "../Plots/output_global2.txt"
this_tests_names <- c(tests_names[8:9])
AZ_names2 <- AZ_names[1:6]
CREATE_QUERIES = TRUE
if (CREATE_QUERIES == TRUE){
  obj<-1
  sink(synk_name3)
  for (az in AZ_names2){ #[1:6]){ 
    if (az == AZ_names2[1]){
      cat("AZ_METRIC_global<-data.frame(\n")
    }
    cat(paste0(az, "<-matrix(c(\n"))
    for(t in this_tests_names){
      cat(c("'", t,"', ", "'",q_cons,"', ", "'",q_slav,"', ", "'",q_energy,"'"), sep = "", append = TRUE)
      if (t != this_tests_names[length(this_tests_names)]){
        cat(",\n")
      }
    }
    obj<-obj+1
    cat("), ncol=4, byrow = TRUE)", append = TRUE)
    if (az != AZ_names2[length(AZ_names2)]){
      cat(",\n")
    }
  }
  cat(")\n", append = TRUE)
  colnames_s<-c()
  for(az in AZ_names2){
    vv<-","
    if (az == AZ_names2[length(AZ_names2)]){
      vv<-""
    }
    colnames_s<- c(colnames_s, paste0("'", az,".alg',","'", az,".q1',","'", az,".q2',","'", az,".q3'",vv))
  }
  ff<-function(vec){
    x=""
    for (e in vec){
      x<-paste0(x,e)
    }
    return(x)
  }
  cat("colnames(AZ_METRIC_global)=(c(", append = TRUE)
  cat(ff(colnames_s))
  cat("))\n", append = TRUE) 
  cat("rownames(AZ_METRIC_global)=this_tests_names\n")
  cat("as.character(AZ_METRIC_global['CHAVE_MAX','AZ1.q1'])\n")
  sink()
  sink()
  source(synk_name3, local = TRUE)
}

source(synk_name3, local = TRUE)
############################## 2.4.1) GENERAL EUCA RADAR CHARTS ##################

print("Executing (24) radar:")
for(az in AZ_names[1:6]){
  print(az)
  fun_g_query <- function(test, query){
    db<-matrix_db[[test, az]]
    resp<-dbGetQuery(db, query)
    return(resp)
  }
  qcol1<-paste0(az,".q1")
  qcol2<-paste0(az,".q2")
  qcol3<-paste0(az,".q3")
  snapshots2<-c()
  df21 <- data.frame(mapply(fun_g_query, this_tests_names, as.character(AZ_METRIC_global[,qcol1])))
  df22 <- data.frame(mapply(fun_g_query, this_tests_names, as.character(AZ_METRIC_global[,qcol2])))
  rownames(df22)="slav"
  colnames(df22)=this_tests_names
  df23 <- data.frame(mapply(fun_g_query, this_tests_names, as.character(AZ_METRIC_global[,qcol3])))
  rownames(df23)="energy_cons"
  colnames(df23)=this_tests_names
  
  dff<-rbind(df21, df22, df23)
  snapshots2<-c(dff)
  
  reduc_val <- sapply(snapshots2,'[[',"reduc_val")
  trigger <- sapply(snapshots2,'[[',"trigger")
  migrations <-sapply(snapshots2,'[[',"migrations")
  fals_pos <-sapply(snapshots2,'[[',"fals_pos")
  slav <-sapply(snapshots2,'[[',5)
  energy_cons <-sapply(snapshots2,'[[',6)/1e6  # Transf to MegaWatts
  
  data <- as.data.frame(matrix( c(reduc_val, trigger, migrations , fals_pos , slav, energy_cons), ncol=6))
  ## Metrics:
  colnames(data)=c("Red(W)", "Trig(n)" , "Mig(n)", "FPos(n)", "Slav(n)", "ET(W)")
  # Tests:
  rownames(data)=this_tests_names
  data=rbind(c(min(reduc_val), max(trigger), max(migrations), max(fals_pos), max(slav), max(energy_cons)), # Max values in range
             c(max(reduc_val), min(trigger), min(migrations), min(fals_pos), min(slav), min(energy_cons)), data) # Min values in range
  #mar is c(bottom, left, top, right)
  par(mar=c(3,4,4,5)+0.1)
  tranp<-1
  colors_border=c( rgb(0.0, 0.0, 1.0, tranp), # blue
                   rgb(0.0, 0.9, 1.0, tranp), # light blue
                   rgb(0.9, 0.0, 0.0, tranp), # red
                   rgb(1.0, 0.7, 0.0, tranp), # orange
                   rgb(0.1, 0.5, 0.1, tranp), # darkgreen
                   rgb(0.3, 0.8, 0.1, tranp), # lightgreen
                   rgb(1.0, 0.2, 0.7, tranp)) # pink
  #rgb(0.0, 0.9, 0.8, tranp))
  #colors_in=c( rgb(0.0,0.0,0.9,0.3),rgb(0.9,0.0,0.0,0.3),rgb(0.9,0.9,0.0,0.3),rgb(0.0,0.6,0.2,0.3),rgb(0.5,0.2,1.0,0.3),rgb(0.0,0.9,0.8,0.3),rgb(0.7,0.8,0.2,0.3))
  line_type=c(1, 5, 1, 5, 1, 5, 1)
  line_pch=c(21, 22, 21, 22, 21, 22, 33)
  line_pch2=c(19, 15, 19, 15, 19, 15, 17)
  mypdf<-paste0("../gen_final_radar_", toString(az), ".pdf")
  pdf(mypdf, title=az, width = 12, height = 7)
  radarchart( data, axistype=1, title=paste("Testes ",az),
              #custom polygon
              pcol=colors_border, plwd=5 , plty=line_type, pty=line_pch2, # , pfcol=colors_in 
              #custom the grid
              cglcol="grey", cglty=1, axislabcol="grey", caxislabels=seq(0,100,25), cglwd=1,
              #custom labels
              vlcex=2 
  )
  #legend(x=1.5, y=1, legend = rownames(data[-c(1,2),]), # horiz=TRUE,
  #       y.intersp=2, x.intersp=1, bty="n", pch=line_pch, lty = line_type, lwd = 3,
  #       col=colors_border, text.col = "black", cex=1.2, pt.cex=4,title=paste("Testes ",az))
  dev.off()
}


############################## 0.6) BASIC QUERIES ###############
# h_av: <- c(0, 20, 40)        # em percentual de requisições
q_replic_attend = "SELECT count(ai) FROM replic_d"
q_replic_add_host = "SELECT count(ai) FROM replic_d WHERE abs(val_0) > 0"
q_replic_add_energy = "SELECT sum(energy_f - energy_0) FROM replic_d"
# cons: <- c(0, 30, 40)        # quantidade de operações realizadas
q_cons = "SELECT count(val_0) FROM consol_d"
q_cons_false_pos = "SELECT count(ai) from consol_d where val_0 = 0"
q_cons_migrations = "SELECT sum(val_f) from consol_d where val_0 > 0"
# energy: <- c(3000, 150, 450)   # em eficiencia/redução total
q_ener = "SELECT sum(val_0)/1000 FROM energy_l"
q_ener_cons = "SELECT sum(energy_0 - energy_f) FROM consol_d"
q_ener_ha = "SELECT sum(energy_0 - energy_f) FROM replic_d"
# load: <- c(60, 75, 90)       # percentual medio de carga
q_avg_load <- 'SELECT avg(val_0)*100 FROM az_load_l'
q_avg_load_max <- 'SELECT max(val_0) FROM az_load_l'
q_avg_load_min <- 'SELECT min(val_0) FROM az_load_l'
q_az_load_val_0 <- 'SELECT val_0 FROM az_load_l'
q_az_load_val_0_gvt <- 'SELECT val_0, gvt FROM az_load_l'
q_energy_load <- 'SELECT val_0 FROM energy_l WHERE gvt=(SELECT gvt FROM az_load_l WHERE val_0 > 0)'
# reject/slav: <- c(0, 3, 9)          # quantidade de rejeições
q_reject = "SELECT count(val_0) FROM reject_l"

######################## DISCONNECT in main func ######################
for(con in az_con_list){
    dbDisconnect(con)
}
#dbDisconnect(con7)

