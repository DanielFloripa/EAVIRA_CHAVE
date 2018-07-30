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
#9     Max          ?   ?   ?   ?   ?   ?   ?     
#10    Max_HA       ?   ?   ?   ?   ?   ?   ?     
#11    EUCA         ?   ?   ?   ?   ?   ?   ? 
# matrix_db[[11,1]] or matrix_db[["EUCA","AZ1"]] or matrix_db["EUCA",] or matrix_db[,"AZ1"]

############################## 0.0) LIBRARIES AND PACKAGES ####
install.packages(c("RSQLite", "ggplot2", "fmsb"),repos = "http://cran.us.r-project.org", quiet=TRUE)
library("fmsb")
library("ggplot2")
library("DBI")
############################## 0.1) MAIN PARAMETERS AND DIRS #################################
# Get the parameter: # date = commandArgs(trailingOnly=TRUE)

path = commandArgs(trailingOnly=TRUE)

if(length(path) == 0 ){
  date = "18.07.03-14.44.35/"
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
matrix_db <- matrix(data=az_con_list, byrow=TRUE, nrow = length(local_tests), ncol = length(AZ_names), dimnames = list(tests_names, AZ_names))
dbListTables(matrix_db[[1,1]])
dbListTables(matrix_db[["EUCA","AZ1"]])
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

############################### QUERY GENERATOR ####################
load_all <- c(25.320513,  0.000000, 72.435897,
                28.571429, 29.761905, 17.857143,
                0.000000,  1.785714,  3.571429,
                8.333333,  0.000000, 33.333333,
                71.471774, 67.439516, 69.758065,
                64.648438, 64.843750, 66.992188)/100
#load_objectives <- c(load_all[1], load_all[4], load_all[9], load_all[10], load_all[13], load_all[16])

#AZ_names2<-c("AZ2", "AZ3", "AZ4")  # az3 menos pior #this_tests_names<-c("Unlock_HA", "Lock_Rand_HA", "Max_HA")

###### APENAS PARA consol_d ####

CREATE_QUERIES = FALSE
if (CREATE_QUERIES == TRUE){
  load_objectives <- c(load_all[1], load_all[13], load_all[16])
  this_tests_names <- c(tests_names[3:8])
  obj<-1
  AZ_names2 <- AZ_names[1:6] #c("AZ1", "AZ2", "AZ5","AZ6")
  synk_name <- "../Plots/output.txt"
  sink(synk_name)
  for (az in AZ_names2){ #[1:6]){ 
      if (obj == 1){
        cat("AZ_ERR_CONS<-data.frame(")
        cat("\n")
      }
      cat(paste0(az, "<-matrix(c("))
      cat("\n")
      for(t in this_tests_names){
          ERR<-0.0001
          ERR_l <- c()
          for(i in seq(1, 9999)){
              qq <- fun_q_join("t.gvt, l.val_0 as load", "consol_d", load_objectives[obj], ERR)
              qq2 <- fun_q_join(metric2, "consol_d", load_objectives[obj], ERR)
              x<-dbGetQuery(matrix_db[[t, az]], qq)
              l<-length(x$load)
              if(l == 0){
                  ERR <- ERR + 0.0001
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
  cat("colnames(AZ_ERR_CONS)=(c(", append = TRUE)
  cat(ff(colnames_s))
  cat("))\n", append = TRUE) #"colnames(AZ_ERR_CONS)=(c('AZ1.alg', 'AZ1.qtd', 'AZ1.err', 'AZ1.query', 'AZ5.alg','AZ5.qtd', 'AZ5.err', 'AZ5.query', 'AZ6.alg', 'AZ6.qtd', 'AZ6.err', 'AZ6.query'))\n", append = TRUE)
  cat("rownames(AZ_ERR_CONS)=this_tests_names\n")
  cat("as.character(AZ_ERR_CONS['CHAVE_MAX','AZ1.err'])\n")
  sink()
  sink()
  source(synk_name, local = TRUE)
}

############################## 2.2) SNAPSHOTS RADAR CHARTS ##################
source(synk_name, local = TRUE)
#source("/home/daniel/Dropbox/UDESC/Mestrado/Pratico/CHAVE-Sim/Plots/databaseRadar_sources.R")
#c("P", "P_HA", "C_AA0", "CHA_AA0", "C_AA20", "CHA_AA20", "C_MAX", "CHA_MAX", "EUCA")
print("Executing radar chart:")
this_az<-AZ_names2
for(az in this_az){
    print(az)
    qcol<-paste0(az,".query")
    fun_g_query <- function(test, query){
        db<-matrix_db[[test, az]]
        resp<-dbGetQuery(db, query)
        return(resp)
    }
    snapshots<-c()
    snapshots <- c(as.data.frame(mapply(fun_g_query, this_tests_names, as.character(AZ_ERR_CONS[,qcol]))))
    
    load <- sapply(snapshots,'[[',"load")
    reducp <-sapply(snapshots,'[[',"reduc_p")
    energyf <-sapply(snapshots,'[[',"energy_f")
    migration <-sapply(snapshots,'[[',"migrations")
    reduc_val <-sapply(snapshots,'[[',"reduc_val")
        
    data <- as.data.frame(matrix( c(load, reducp, energyf , migration , reduc_val), ncol=5))
    ## Metrics:
    colnames(data)=c("Carga (%)" , "Redução (%)", "Energia Total (W)", "Nº Migrações", "Redução (W)")
    # Tests:
    rownames(data)=this_tests_names
    ## To use the fmsb package, I have to add 2 lines to the dataframe: the max and min of each topic to show on the plot!
    data=rbind(c(max(load), max(reducp), max(energyf), max(migration), max(reduc_val)), # Max values in range
               c(min(load), min(reducp), min(energyf), min(migration), min(reduc_val)), data)                     # Min values in range
    #mar=c(bottom, left, top, right)
    par(mar=c(3,4,4,4)+0.1)
    tranp<-1
    colors_border=c( rgb(0.0, 0.0, 1.0, tranp), # blue
                     rgb(0.0, 0.9, 1.0, tranp), # light blue
                     rgb(0.9, 0.0, 0.0, tranp), # red
                     rgb(1.0, 0.7, 0.0, tranp), # orange
                     rgb(0.1, 0.4, 0.3, tranp), # darkgreen
                     rgb(0.3, 0.8, 0.1, tranp), # lightgreen
                     rgb(1.0, 0.2, 0.7, tranp)) # pink
                     #rgb(0.0, 0.9, 0.8, tranp))
    #colors_in=c( rgb(0.0,0.0,0.9,0.3),rgb(0.9,0.0,0.0,0.3),rgb(0.9,0.9,0.0,0.3),rgb(0.0,0.6,0.2,0.3),rgb(0.5,0.2,1.0,0.3),rgb(0.0,0.9,0.8,0.3),rgb(0.7,0.8,0.2,0.3))
    line_type=c(1, 1, 2, 2, 4, 4, 5)
    line_pch=c(21, 22, 21, 22, 21, 22, 33)
    op <- par(cex = 2)
    mypdf<-paste0("../radar_", toString(az), ".pdf")
    pdf(mypdf, title=mypdf, width = 9, height = 6)
    radarchart( data, axistype=1, 
                #custom polygon
                pcol=colors_border, plwd=5 , plty=line_type, # , pfcol=colors_in 
                #custom the grid
                cglcol="grey", cglty=1, axislabcol="grey", caxislabels=seq(0,100,25), cglwd=1,
                #custom labels
                vlcex=1.2 
    )
    legend(x=1.5, y=1.5, legend = rownames(data[-c(1,2),]), 
           y.intersp=2, x.intersp=1, bty="n", pch=line_pch, lty = line_type, lwd = 3,
           col=colors_border, text.col = "black", cex=1, pt.cex=5,title="Testes")
    dev.off()
}

############################## 2.3) GENERAL RADAR CHARTS ##################
this_test <-c("EUCA", "Max_HA", "Place_HA", "Lock_Rand_HA")
this_query <- c(q_replic_attend, q_cons, q_ener, q_avg_load, q_reject)

radar2 <- function(az, azmat){
    fun_g_query <- function(test, query){
        db<-matrix_db[[test, az]]
        resp<-dbGetQuery(db, query)
        #dput(resp)
        return(resp)
    }
    h_av <- c(as.double(mapply(fun_g_query, this_test, rep(this_query[1], length(this_test)))))
    cons <- c(as.double(mapply(fun_g_query, this_test, rep(this_query[2], length(this_test)))))
    ener <- c(as.double(mapply(fun_g_query, this_test, rep(this_query[3], length(this_test)))))
    load <- c(as.double(mapply(fun_g_query, this_test, rep(this_query[4], length(this_test)))))
    slav <- c(as.double(mapply(fun_g_query, this_test, rep(this_query[5], length(this_test)))))
    #fun_g_query(azmat[i,1], azmat[i,4]))
    

    data <- as.data.frame(matrix( c(h_av, cons, ener, load, slav), ncol=5))
    ## Metrics:
    colnames(data)=c("Alta Disp." , "Consolidações", "Consumo Energia", "Carga", "Rejeições")
    ## Tests:
    rownames(data)=this_test
    ## To use the fmsb package, I have to add 2 lines to the dataframe: the max and min of each topic to show on the plot!
    data=rbind(c(max(h_av), max(cons), max(ener), 100, max(slav)), # Max values in range
               c(0, 0, 0, 0, 0), data)                     # Min values in range
    par(mar=c(5,4,4,2)+0.1)
    colors_border=c( rgb(0.0,0.0,0.9,0.9),
                     rgb(0.9,0.0,0.0,0.9),
                     rgb(0.9,0.9,0.0,0.9),
                     rgb(0.0,0.6,0.2,0.9) )
    colors_in=c( rgb(0.0,0.0,0.9,0.4),
                 rgb(0.9,0.0,0.0,0.4),
                 rgb(0.9,0.9,0.0,0.4),
                 rgb(0.0,0.6,0.2,0.4) )
    line_type=c(1,2,3,4)
    pdf(paste0("../radar2_", toString(az), ".pdf"), width = 9, height = 5)
    radarchart( data, axistype=1, 
                #custom polygon
                pcol=colors_border , pfcol=colors_in , plwd=line_type , plty=line_type,
                #custom the grid
                cglcol="grey", cglty=1, axislabcol="grey", caxislabels=seq(0,100,25), cglwd=1,
                #custom labels
                vlcex=1.2 
    )
    legend(x=1.5, y=1, legend = rownames(data[-c(1,2),]), 
           y.intersp=2, x.intersp=1, bty="n", pch=20 , 
           col=colors_border, text.col = "black", cex=1, pt.cex=5,
           title="Testes")
    dev.off()
}

print("Executing (23) radar2:")
for(az in AZ_names[1:6]){
    print(az)
    radar2(az)
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


########################### 0.7 QUERIES FOR SNAPSHOTS ####################
fun_q_join<-function(metric, table, load, error){
    return(paste0("SELECT ", toString(metric), " FROM ", toString(table), 
                  " as t inner join az_load_l as l on l. gvt=t.gvt and (l.val_0 < ", 
                  toString(load+error)," and l.val_0 > ", toString(load-error),")"))
}
qs_cons <- fun_q_join("t.gvt, l.val_0 as load", "consol_d", load_objectives[1], 0.05)
############################## 2.4) ONE CASE RADAR CHARTS ##################
this_test <-c("EUCA", "Max_HA", "Place_HA", "Lock_Rand_HA")
#this_query <- c(q_replic_attend, q_cons, q_ener, q_avg_load, q_reject)
this_query <- c(q_replic_attend, qs_cons, q_ener, q_avg_load, q_reject)
az="AZ1"; azid=1

radar3 <- function(az){
  az<-"AZ1"
    fun_g_query <- function(test, query){
        db<-matrix_db[[test, az]]
        res<-dbGetQuery(db, query)
        if(length(res[[1]]) == 0){
          res<-replicate(length(this_test), 0)
        }
        return(res)
    }
    h_av <- c(as.double(mapply(fun_g_query, this_test, rep(this_query[1], length(this_test)))))
    cons <- c(as.double(mapply(fun_g_query, this_test, rep(this_query[2], length(this_test)))))
    ener <- c(as.double(mapply(fun_g_query, this_test, rep(this_query[3], length(this_test)))))
    load <- c(as.double(mapply(fun_g_query, this_test, rep(this_query[4], length(this_test)))))
    slav <- c(as.double(mapply(fun_g_query, this_test, rep(this_query[5], length(this_test)))))
    
    data <- as.data.frame(matrix( c(h_av,cons,ener,load,slav), ncol=5))
    ## Metrics:
    #colnames(data)=c("Alta Disp." , "Consolidações", "Consumo Energia", "Carga", "Rejeições")
    colnames(data)=c("Alta Disp." , "Consolidações", "Consumo Energia", "Carga", "Rejeições")
    ## Tests:
    rwnames(data)=this_test
    ## To use the fmsb package, I have to add 2 lines to the dataframe: the max and min of each topic to show on the plot!
    data=rbind(c(max(h_av), max(cons), max(ener), 100, max(slav)), # Max values in range
               c(0, 0, 0, 0, 0), data)                     # Min values in range
    par(mar=c(5,4,4,2)+0.1)
    colors_border=c( rgb(0.0,0.0,0.9,0.9),
                     rgb(0.9,0.0,0.0,0.9),
                     rgb(0.9,0.9,0.0,0.9),
                     rgb(0.0,0.6,0.2,0.9) )
    colors_in=c( rgb(0.0,0.0,0.9,0.4),
                 rgb(0.9,0.0,0.0,0.4),
                 rgb(0.9,0.9,0.0,0.4),
                 rgb(0.0,0.6,0.2,0.4) )
    line_type=c(1,2,3,4)
    pdf(paste0("radar_", toString(az), ".pdf"), width = 9, height = 5)
    radarchart( data, axistype=1, 
                #custom polygon
                pcol=colors_border , pfcol=colors_in , plwd=line_type , plty=line_type,
                #custom the grid
                cglcol="grey", cglty=1, axislabcol="grey", caxislabels=seq(0,100,25), cglwd=1,
                #custom labels
                vlcex=1.2 
    )
    legend(x=1.5, y=1, legend = rownames(data[-c(1,2),]), 
           y.intersp=2, x.intersp=1, bty="n", pch=20 , 
           col=colors_border, text.col = "black", cex=1, pt.cex=5,
           title="Testes")
    dev.off()
}

print("Executing radar chart:")
for(az in AZ_names[1:6]){
    print(az)
    radar3(az)
}
######################## DISCONNECT in main func ######################
for(con in az_con_list){
    dbDisconnect(con)
}
#dbDisconnect(con7)

