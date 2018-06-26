#install.packages(c("RSQLite", "ggplot2"))
library("ggplot2")
library(DBI)
############################## MAIN PARAMETERS AND DIRS #################################
# Get the parameter:
# date = commandArgs(trailingOnly=TRUE)
date = "18.06.21-12.33.48"
pwd <- "/home/daniel/"
#date = "18.06.21-11.08.24" #"18.06.21-12.33.48"
#pwd <- "~/Dropbox/UDESC/Mestrado/Pratico/CHAVE-Sim/output/"
"EUCA_CF_L:None_O:False_C:False_R:False"
rdef <- paste0(toString(pwd), toString("/results/"))
rootEUCA <- paste0(toString(pwd), toString("EUCA_CF_L:None_O:False_C:False_R:False/"))
##############################CHOOSE THE DIRECTORY#####################
root=rootEUCA
out <- tryCatch({
    setwd(root)
},
error=function(cond){
    message("ERROR:")
    message(root)
},
warning=function(cond){
    message("WARNING:")
    message(root)
},
finnaly={
    message("Change dir to: ")
    print(root)
})
##############################__SELECT THE DB_FILES___##################################################
f <- list.files(pattern="*.db") # , ignore.case = TRUE)
azs <- c("AZ1", "AZ2", "AZ3", "AZ4", "AZ5", "AZ6")

for(files in f){
    #testFiles(f)
    for(ff in files){
        if(!file.exists(ff)){
            message("ERROR ON: ")
            message(ff)
        }
        print(ff)
    }
}
##############################___CONECTIONS___#############################################
con1 <- dbConnect(RSQLite::SQLite(), f[1])
con2 <- dbConnect(RSQLite::SQLite(), f[2])
con3 <- dbConnect(RSQLite::SQLite(), f[3])
con4 <- dbConnect(RSQLite::SQLite(), f[4])
con5 <- dbConnect(RSQLite::SQLite(), f[5])
con6 <- dbConnect(RSQLite::SQLite(), f[6])
az_con_list <- c(con1, con2, con3, con4, con5, con6)
#con7 <- dbConnect(RSQLite::SQLite(), f[7])
metrics <- dbListTables(con1); metrics
############################ FUNCTIONS ###############################
result <- function(query){
    res1 <-dbGetQuery(con1, query)
    res2 <-dbGetQuery(con2, query)
    res3 <-dbGetQuery(con3, query)
    res4 <-dbGetQuery(con4, query)
    res5 <-dbGetQuery(con5, query)
    res6 <-dbGetQuery(con6, query)
    print(c(res1, res2, res3, res4, res5, res6))
    resp <-c(res1[[1]], res2[[1]], res3[[1]], res4[[1]], res5[[1]], res6[[1]])
    return(resp)
}
result_sd <- function(query){
    res1 <-dbGetQuery(con1, query)
    res2 <-dbGetQuery(con2, query)
    res3 <-dbGetQuery(con3, query)
    res4 <-dbGetQuery(con4, query)
    res5 <-dbGetQuery(con5, query)
    res6 <-dbGetQuery(con6, query)
    resp <-c(sd(res1[[1]]), sd(res2[[1]]), sd(res3[[1]]), sd(res4[[1]]), sd(res5[[1]]), sd(res6[[1]]))
    return(resp)
}
############### ALL QUERIES ###############
q_avg_load <- 'SELECT avg(val_0) FROM az_load_l'
q_avg_load_max <- 'SELECT max(val_0) FROM az_load_l'
q_avg_load_min <- 'SELECT min(val_0) FROM az_load_l'
q_avg_load25 <- 'SELECT val_0 FROM az_load_l where val_0 >= 24 and val_0 <= 26'
q_az_load_val_0 <- 'SELECT val_0 FROM az_load_l'
q_energy_all = 'SELECT * FROM energy_l'
q_energy_load = 'select val_0 from energy_l where gvt=(select gvt from az_load_l where val_0 > 0)'

gen_energy_load <- function(base, range){
    q = "select val_0 from energy_l where gvt=(select gvt from az_load_l where val_0 > "
    resp <- paste0(toString(q), toString(base-range), toString(" and val_0 < "), toString(base+range), toString(")"))
    return(resp)   
}
######################### AVG AZ LOAD #######################
data1 <- data.frame(
    AZ = azs,
    Load = result(q_avg_load),
    std = result_sd(q_az_load_val_0)
)
pdf("Mean_Load_AZs.pdf", width=7, height=7)
ggplot(data1) +
    geom_bar(aes(x=AZ, y=Load), stat="identity", fill="blue", alpha=0.9) +
    geom_errorbar(aes(x=AZ, ymin=Load-std, ymax=Load+std), width=0.4, colour="orange", alpha=0.9, size=1.3)
dev.off()

######################### MAX AZ LOAD #######################
data1 <- data.frame(
    AZ = azs,
    Load = result(q_avg_load_max)
)
pdf("MAX_Load_AZs.pdf", width=7, height=5)
ggplot(data1) +
    geom_bar(aes(x=AZ, y=Load), stat="identity", fill="blue", alpha=0.9)
dev.off()

######################### 1) energy LOAD #######################

qdmin = "select energy_l.val_0 from energy_l inner join az_load_l on energy_l.gvt = az_load_l.gvt and az_load_l.val_0 < :x"
qdmid = "select energy_l.val_0 from energy_l inner join az_load_l on energy_l.gvt = az_load_l.gvt and (az_load_l.val_0 > :x and az_load_l.val_0 < :y)"
qdmax = "select energy_l.val_0 from energy_l inner join az_load_l on energy_l.gvt = az_load_l.gvt and az_load_l.val_0 > :x"
loads = c("08","08-12","28-22","28-32","38-42","48-52","58-62","68-72","78-82","82")

leg<-function(xx_min, xx_max, err){
    resp<-c(xx_min-err)
    for (i in xx_min:xx_max){
        l<-paste0(toString(i-err), toString("-"), toString(i+err))
        resp<-c(resp,l)
    }
    resp<-c(resp,xx_max+err)
    return(resp)
}
print(leg(0.1, 0.9, 0.02))

fun_load_energy_min<-function(conaz, xx){
    Loadd1<-c()
    res1 <- dbSendQuery(conaz, qdmin, params=c(x=xx))
    while(!dbHasCompleted(res1)){
        chunk <- dbFetch(res1, n = 1000)$val_0
        Loadd1<-c(Loadd1, as.numeric(chunk))
    }
    dbClearResult(res1)
    if (length(Loadd1) == 0)
        return(c(1,1))
    return(Loadd1)
}

fun_load_energy_mid<-function(conaz, xx, yy){
    Loadd2<-c()
    res2 <- dbSendQuery(conaz, qdmid, params=c(x=xx, y=yy))
    while(!dbHasCompleted(res2)){
        chunk <- dbFetch(res2, n = 1000)$val_0
        Loadd2<-c(Loadd2, as.numeric(chunk))
    }
    dbClearResult(res2)
    if (length(Loadd2) == 0)
        return(c(1,1))
    return(Loadd2)
}

fun_load_energy_max<-function(conaz, xx){
    Loadd3<-c()
    res3 <- dbSendQuery(conaz, qdmax, params=c(x=xx))
    while(!dbHasCompleted(res3)){
        chunk <- dbFetch(res3, n = 1000)$val_0
        Loadd3<-c(Loadd3, as.numeric(chunk))
    }
    dbClearResult(res3)
    if (length(Loadd3) == 0)
        return(c(1,1))
    return(Loadd3)
}

fun_load_energy_each_az <- function(con_az, i){
    print(i)
    
    Load1 <- fun_load_energy_min(con_az, 0.08)
    Load2 <- fun_load_energy_mid(con_az, xx=0.05, yy=0.15)
    Load3 <- fun_load_energy_mid(con_az, xx=0.15, yy=0.25)
    Load4 <- fun_load_energy_mid(con_az, xx=0.25, yy=0.35)
    Load5 <- fun_load_energy_mid(con_az, xx=0.35, yy=0.45)
    Load6 <- fun_load_energy_mid(con_az, xx=0.45, yy=0.55)
    Load7 <- fun_load_energy_mid(con_az, xx=0.55, yy=0.65)
    Load8 <- fun_load_energy_mid(con_az, xx=0.65, yy=0.75)
    Load9 <- fun_load_energy_mid(con_az, xx=0.75, yy=0.85)
    Load10 <- fun_load_energy_max(con_az, xx=0.85)
    
    data_el <- data.frame(
        Legends = loads,
        Energy = c(mean(Load1, na.rm = TRUE), mean(Load2, na.rm = TRUE), mean(Load3, na.rm = TRUE), mean(Load4, na.rm = TRUE), mean(Load5, na.rm = TRUE), mean(Load6, na.rm = TRUE), mean(Load7, na.rm = TRUE), mean(Load8, na.rm = TRUE), mean(Load9, na.rm = TRUE), mean(Load10, na.rm = TRUE)),
        std = c(sd(Load1), sd(Load2), sd(Load3), sd(Load4), sd(Load5), sd(Load6), sd(Load7), sd(Load8), sd(Load9), sd(Load10))
    )
    print(data_el$Energy)
    pdf_name <- paste0(toString("Load_Energy_AZ"), toString(i), toString(".pdf"))
    #pdf(pdf_name, width=17, height=15)
    ggplot(data=data_el) +
        geom_bar(aes(x=Legends, y=Energy), fill="blue", alpha=0.9, stat="identity") +
        geom_errorbar(aes(x=Legends, ymin=Energy-std, ymax=Energy+std), width=0.4, colour="orange", alpha=0.9, size=1)  #+ ggtitle(pdf_name)
    ggsave(pdf_name)
}

i<-1
for (az_con in az_con_list){
    fun_load_energy_each_az(az_con, i)
    i<-i+1
}

######################### 1) SCATTER PLOT #######################
fun_scatter_each_az <- function(con_az, i){
    
    load=dbGetQuery(con_az, q_az_load_val_0)$val_0
    gvt=seq(1:length(load))
    
    pdf_name <- paste0(toString("Hist_AZ"), toString(i), toString(".pdf"))
    pdf(pdf_name, width=7, height=5)
    hist(load,  main="" , breaks=10 , col=rgb(0.3,0.5,0.9,0.4) , xlab="AZ_Load" , ylab="Frequency")
    dev.off()
    
    pdf_name <- paste0(toString("Scatter_AZ"), toString(i), toString(".pdf"))
    pdf(pdf_name, width=7, height=5)
    plot(gvt, load ,  pch=1 , bg="white" , cex=1 , col=rgb(0.1,0.3,0.5,0.5), ylab="AZ_Load" , xlab="Time" )
    mtext("Scatter Load GVT", outer = TRUE, cex = 1, font=4, col=rgb(0.1,0.3,0.5,0.5))
    dev.off()
}

i<-1
for (az_con in az_con_list){
    print(i)
    fun_scatter_each_az(az_con, i)
    i<-i+1
}
######################___ QUERY ENERGY ___#############################
query_energy = 'SELECT * FROM energy_l'
avg_energy1 <-dbGetQuery(con1, query_energy)
avg_energy2 <-dbGetQuery(con2, query_energy)
avg_energy3 <-dbGetQuery(con3, query_energy)
avg_energy4 <-dbGetQuery(con4, query_energy)
avg_energy5 <-dbGetQuery(con5, query_energy)
avg_energy6 <-dbGetQuery(con6, query_energy)

########################ENERGY AZ1#####################################
data2 <- data.frame(
    Time <- avg_energy2$gvt,
    Energy <- avg_energy2$val_0
)
pdf("Energy2.pdf", width=7, height=5)
ggplot(data=data2, aes(x=Time, y=Energy), stat="identity", fill="blue", alpha=0.9) +
    geom_line()+
    geom_point()
dev.off()
########################ENERGY AZ2#####################################
data2 <- data.frame(
    Time <- avg_energy2$gvt,
    Energy <- avg_energy2$val_0
)
pdf("Energy2.pdf", width=7, height=5)
ggplot(data=data2, aes(x=Time, y=Energy), stat="identity", fill="blue", alpha=0.9) +
    geom_line()+
    geom_point()
dev.off()
########################ENERGY AZ3#####################################
data2 <- data.frame(
    Time <- avg_energy3$gvt,
    Energy <- avg_energy3$val_0
)
pdf("Energy3.pdf", width=7, height=5)
ggplot(data=data2, aes(x=Time, y=Energy), stat="identity", fill="blue", alpha=0.9) +
    geom_line()+
    geom_point()
dev.off()
########################ENERGY AZ4#####################################
data2 <- data.frame(
    Time <- avg_energy4$gvt,
    Energy <- avg_energy4$val_0
)
pdf("Energy4.pdf", width=7, height=5)
ggplot(data=data2, aes(x=Time, y=Energy), stat="identity", fill="blue", alpha=0.9) +
    geom_line()+
    geom_point()
dev.off()
########################ENERGY AZ5#####################################
data2 <- data.frame(
    Time <- avg_energy5$gvt,
    Energy <- avg_energy5$val_0
)
pdf("Energy5.pdf", width=7, height=5)
ggplot(data=data2, aes(x=Time, y=Energy), stat="identity", fill="blue", alpha=0.9) +
    geom_line()+
    geom_point()
dev.off()
########################ENERGY AZ6#####################################
data2 <- data.frame(
    Time <- avg_energy6$gvt,
    Energy <- avg_energy6$val_0
)
pdf("Energy6.pdf", width=7, height=5)
ggplot(data=data2, aes(x=Time, y=Energy), stat="identity", fill="blue", alpha=0.9) +
    geom_line()+
    geom_point()
dev.off()

###########################___ QUERY CONSOL_D ___#####################################################
query_energy = 'SELECT * FROM consol_d where val_0=1'

avg_energy1 <-dbGetQuery(con1, query_energy)
avg_energy2 <-dbGetQuery(con2, query_energy)
avg_energy3 <-dbGetQuery(con3, query_energy)
avg_energy4 <-dbGetQuery(con4, query_energy)
avg_energy5 <-dbGetQuery(con5, query_energy)
avg_energy6 <-dbGetQuery(con6, query_energy)

data2 <- data.frame(
    Time <- avg_energy6$gvt,
    Energy <- avg_energy6$val_1
)
pdf("consol_d_az6.pdf", width=7, height=5)
ggplot(data=data2, aes(x=Time, y=Energy), stat="identity", fill="blue", alpha=0.9) +
    geom_line()+
    geom_point()
dev.off()

######################## DISCONNECT ######################
dbDisconnect(con1)
dbDisconnect(con2)
dbDisconnect(con3)
dbDisconnect(con4)
dbDisconnect(con5)
dbDisconnect(con6)
dbDisconnect(con7)

