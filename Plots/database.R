#install.packages(c("RSQLite", "ggplot2"))
library("ggplot2")
library(DBI)
############################## MAIN PARAMETERS AND DIRS #################################
# Get the parameter:
# date = commandArgs(trailingOnly=TRUE)
#date = "18.06.21-11.08.24" #"18.06.21-12.33.48"
date = "18.06.21-12.33.48/"
#pwd <- "/home/daniel/output/"
pwd <- "/media/debian/"
#pwd <- "~/Dropbox/UDESC/Mestrado/Pratico/CHAVE-Sim/output/"
test <- "EUCA_CF_L:None_O:False_C:False_R:False"
#meta <- "CHAVE_LOCK_L:RANDOM_O:False_C:True_R:False"
rdef <- paste0(toString(pwd), toString(date[1])) #, toString("results/"))
root <- paste0(toString(rdef), toString(test))
############################## CHOOSE THE DIRECTORY #####################
print(root)
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
############################## TEST THE DB_FILES ##################################################
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
############################ CDF ###############################
sample.data = c(Delay=rnorm(10000))
cdf <- ggplot (data=sample.data, aes(x=Delay, group =Type, color = Type)) + stat_ecdf()
cdf

x <- rnorm(10000)
plot(ecdf(x))






############################ BASIC FUNCTIONS ###############################
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
############### BASIC QUERIES ###############
q_avg_load <- 'SELECT avg(val_0) FROM az_load_l'
q_avg_load_max <- 'SELECT max(val_0) FROM az_load_l'
q_avg_load_min <- 'SELECT min(val_0) FROM az_load_l'
q_avg_load25 <- 'SELECT val_0 FROM az_load_l where val_0 >= 24 and val_0 <= 26'
q_az_load_val_0 <- 'SELECT val_0 FROM az_load_l'
q_energy_all = 'SELECT * FROM energy_l'
q_energy_load = 'select val_0 from energy_l where gvt=(select gvt from az_load_l where val_0 > 0)'

######################### AVG AZ LOAD #######################
data1 <- data.frame(
    AZ = azs,
    Load = result(q_avg_load),
    std = result_sd(q_az_load_val_0)
)
pdf("00-Mean_Load_AZs.pdf", width=7, height=7)
ggplot(data1) +
    geom_bar(aes(x=AZ, y=Load), stat="identity", fill="blue", alpha=0.9) +
    geom_errorbar(aes(x=AZ, ymin=Load-std, ymax=Load+std), width=0.4, colour="orange", alpha=0.9, size=1.3)
dev.off()

######################### MAX AZ LOAD #######################
data1 <- data.frame(
    AZ = azs,
    Load = result(q_avg_load_max)
)
pdf("01-MAX_Load_AZs.pdf", width=7, height=5)
ggplot(data1) +
    geom_bar(aes(x=AZ, y=Load), stat="identity", fill="blue", alpha=0.9)
dev.off()
######################### 02) SCATTER PLOT #######################
#fun_scatter_each_az <- function(con_az, i){
#    load=dbGetQuery(con_az, q_az_load_val_0)$val_0
#    gvt=seq(1:length(load))
#    BREAKS<-20
#    pdf_name <- paste0(toString("02-Hist_AZ"), toString(i), toString(BREAKS), toString(".pdf"))
#    pdf(pdf_name, width=7, height=5)
#    hist(load,  main="" , breaks=BREAKS, col=rgb(0.3,0.5,0.9,0.4) , xlab="AZ_Load" , ylab="Frequency")
#    dev.off()
#    plot_name <- paste0(toString("03-Scatter_AZ"), toString(i))
#    pdf_name <- paste0(toString(plot_name), toString(".pdf"))
#    pdf(pdf_name, width=7, height=5)
#    plot(gvt, load ,  pch=1 , bg="white" , cex=1 , col=rgb(0.1,0.3,0.5,0.5), ylab="AZ_Load" , xlab="Time" )
#    mtext(plot_name, outer = TRUE, cex = 1, font=4, col=rgb(0.1,0.3,0.5,0.5))
#    dev.off()
#}
fun_scatter_each_az <- function(con_az, i){
    dat <- data.frame(
        load=dbGetQuery(con_az, q_az_load_val_0)$val_0,
        gvt=seq(1:length(load))
    )
    # HIST:
    BREAKS<-20
    plot_name1 <- paste0(toString("02-Hist_AZ"), toString(i), toString(BREAKS))
    pdf_name1 <- paste0(toString(plot_name1), toString(".pdf"))
    ggplot(dat, aes(dat$load))+
        geom_histogram(bins=BREAKS)
    ggsave(pdf_name1)
    # SCATTER:
    #plot_name <- paste0(toString("03-Scatter_AZ"), toString(i))
    #pdf_name <- paste0(toString(plot_name), toString(".pdf"))
    #plot(gvt, load ,  pch=1 , bg="white" , cex=1 , col=rgb(0.1,0.3,0.5,0.5), ylab="AZ_Load" , xlab="Time" )
    #ggplot(dat, aes(x=gvt, y=load)) +
    #    geom_point(shape=1) +    # Use hollow circles
    #    geom_smooth(method=lm)#+ggtitle(plot_name)+xlab("Time") + ylab("Load")
    #ggsave(pdf_name)
}
i<-1
for (az_con in az_con_list){
    print(i)
    fun_scatter_each_az(az_con, i)
    i<-i+1
}
######################### LOAD AND ENERGY #######################

qdmin = "select energy_l.val_0 from energy_l inner join az_load_l on energy_l.gvt = az_load_l.gvt and az_load_l.val_0 < :x"
qdmid = "select energy_l.val_0 from energy_l inner join az_load_l on energy_l.gvt = az_load_l.gvt and (az_load_l.val_0 > :x and az_load_l.val_0 < :y)"
qdmax = "select energy_l.val_0 from energy_l inner join az_load_l on energy_l.gvt = az_load_l.gvt and az_load_l.val_0 > :x"
#loads = c("08","08-12","28-22","28-32","38-42","48-52","58-62","68-72","78-82","82")

leg<-function(xmin, xmax, err, incr, has_boarders=FALSE){
    resp<-c()
    if (has_boarders == TRUE){ resp<-c(xmin-err)}
    for (i in seq(xmin,xmax, incr)){
        l<-paste0(toString(i-err), toString("-"), toString(i+err))
        resp<-c(resp,l)
    }
    if (has_boarders == TRUE){resp<-c(resp,xmax+err)}
    return(resp)
}
#print(leg(0.25, 0.75, 0.02, 0.25, TRUE))

print(leg(0.1, 0.8, 0.02, 0.1, TRUE))
fun_load_energy_min<-function(conaz, xx, err){
    Loadd1<-c()
    res1 <- dbSendQuery(conaz, qdmin, params=c(x=xx-err))
    while(!dbHasCompleted(res1)){
        chunk <- dbFetch(res1, n = 1000)$val_0
        Loadd1<-c(Loadd1, as.numeric(chunk))
    }
    dbClearResult(res1)
    if (length(Loadd1) == 0)
        return(c(1,1))
    return(Loadd1)
}

fun_load_energy_mid<-function(conaz, xx, err){
    Loadd2<-c()
    res2 <- dbSendQuery(conaz, qdmid, params=c(x=xx-err, y=xx+err))
    while(!dbHasCompleted(res2)){
        chunk <- dbFetch(res2, n = 1000)$val_0
        Loadd2<-c(Loadd2, as.numeric(chunk))
    }
    dbClearResult(res2)
    if (length(Loadd2) == 0)
        return(c(1,1))
    return(Loadd2)
}

fun_load_energy_max<-function(conaz, xx, err){
    Loadd3<-c()
    res3 <- dbSendQuery(conaz, qdmax, params=c(x=xx+err))
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
    ERR <- 0.02
    INCR <- 0.1
    Load1 <- fun_load_energy_min(con_az, xx=0.1, err=ERR)
    Load2 <- fun_load_energy_mid(con_az, xx=0.2, err=ERR)
    Load3 <- fun_load_energy_mid(con_az, xx=0.3, err=ERR)
    Load4 <- fun_load_energy_mid(con_az, xx=0.4, err=ERR)
    Load5 <- fun_load_energy_mid(con_az, xx=0.5, err=ERR)
    Load6 <- fun_load_energy_mid(con_az, xx=0.6, err=ERR)
    Load7 <- fun_load_energy_mid(con_az, xx=0.7, err=ERR)
    Load8 <- fun_load_energy_mid(con_az, xx=0.8, err=ERR)
    Load9 <- fun_load_energy_mid(con_az, xx=0.9, err=ERR)
    Load10 <- fun_load_energy_max(con_az, xx=0.9, err=ERR)
    
    data_el <- data.frame(
        Legends = leg(0.1, 0.8, ERR, INCR, TRUE),
        Energy = c(mean(Load1, na.rm = TRUE), mean(Load2, na.rm = TRUE), mean(Load3, na.rm = TRUE), mean(Load4, na.rm = TRUE), mean(Load5, na.rm = TRUE), mean(Load6, na.rm = TRUE), mean(Load7, na.rm = TRUE), mean(Load8, na.rm = TRUE), mean(Load9, na.rm = TRUE), mean(Load10, na.rm = TRUE)),
        std = c(sd(Load1), sd(Load2), sd(Load3), sd(Load4), sd(Load5), sd(Load6), sd(Load7), sd(Load8), sd(Load9), sd(Load10))
    )
    plot_name <- paste0(toString("10-Load_Energy_AZ"), toString(i), toString(ERR), toString(INCR))
    pdf_name <- paste0(toString(plot_name), toString(".pdf"))
    ggplot(data=data_el) +
        geom_bar(aes(x=Legends, y=Energy), fill="blue", alpha=0.9, stat="identity") +
        geom_errorbar(aes(x=Legends, ymin=Energy-std, ymax=Energy+std), width=0.4, colour="orange", alpha=0.9, size=1)+
        ggtitle(plot_name)
    ggsave(pdf_name)
}
i<-1
for (az_con in az_con_list){
    fun_load_energy_each_az(az_con, i)
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
#dbDisconnect(con7)

