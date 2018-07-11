#!/usr/bin/env Rscript
###############################################
#### This R is part of CHAVE-SIM Project    ###
#### Avalable at dscar.ga/chave             ###
###############################################
############################## 0.0) LIBRARIES AND PACKAGES ####
#install.packages(c("RSQLite", "ggplot2", "fmsb"),repos = "http://cran.us.r-project.org")#, "plyr","reshape2")
#install.packages("tidyverse")
#library(tidyverse)
#library("plyr")
#library("reshape2")
library("fmsb")
library("ggplot2")
library(DBI)
############################## 0.1) MAIN PARAMETERS AND DIRS #################################
# Get the parameter:
# date = commandArgs(trailingOnly=TRUE)
date = "18.06.27-12.42.39/"
#date = "18.07.02-22.55.25/"
pwd <- "/home/daniel/output/"
#pwd <- "/media/debian/"
#pwd <- "~/Dropbox/UDESC/Mestrado/Pratico/CHAVE-Sim/output/"
test <- "EUCA_CF_L:None_O:False_C:False_R:False/"
#test <- "CHAVE_LOCK_L:RANDOM_O:False_C:True_R:False/"

test_l <- c("EUCA_CF_L:None_O:False_C:False_R:False",
            "CHAVE_CF_L:None_O:False_C:False_R:False",
            "CHAVE_LOCK_L:RANDOM_O:False_C:True_R:False",
            "CHAVE_MAX_L:None_O:False_C:True_R:False",
            "CHAVE_LOCK_L:False_O:False_C:True_R:False",
            "CHAVE_LOCK_L:True_O:False_C:True_R:False",
            "CHAVE_LOCK_L:False_O:False_C:True_R:True",
            "CHAVE_LOCK_L:True_O:False_C:True_R:True",
            "CHAVE_LOCK_L:RANDOM_O:False_C:True_R:True",
            "CHAVE_MAX_L:None_O:False_C:True_R:True",
            "CHAVE_CF_L:None_O:False_C:False_R:True"
            
)

main<-function(test){
rdef <- paste0(toString(pwd), toString(date[1]), toString("results/"))
root <- paste0(toString(rdef), toString(test))
############################## 0.2) CHOOSE THE DIRECTORY #####################
#print(root)
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
############################## 0.3) TEST THE DB_FILES ##################################################
f <- list.files(pattern="*.db") # , ignore.case = TRUE)
azs <- c("AZ1", "AZ2", "AZ3", "AZ4", "AZ5", "AZ6")
for(files in f){
    for(ff in files){
      if(!file.exists(ff)){
          message("ERROR ON: ")
          message(ff)
      }
      print(ff)
  }
}
############################## 0.4) CONECTIONS #############################################
con1 <- dbConnect(RSQLite::SQLite(), f[1])
con2 <- dbConnect(RSQLite::SQLite(), f[2])
con3 <- dbConnect(RSQLite::SQLite(), f[3])
con4 <- dbConnect(RSQLite::SQLite(), f[4])
con5 <- dbConnect(RSQLite::SQLite(), f[5])
con6 <- dbConnect(RSQLite::SQLite(), f[6])
az_con_list <- c(con1, con2, con3, con4, con5, con6)
#con7 <- dbConnect(RSQLite::SQLite(), f[7])
metrics <- dbListTables(con1); metrics
############################## 0.5) BASIC FUNCTIONS ###############################
result <- function(query){
    res1 <-dbGetQuery(con1, query)
    res2 <-dbGetQuery(con2, query)
    res3 <-dbGetQuery(con3, query)
    res4 <-dbGetQuery(con4, query)
    res5 <-dbGetQuery(con5, query)
    res6 <-dbGetQuery(con6, query)
    #print(c(res1, res2, res3, res4, res5, res6))
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
############################## 0.6) BASIC QUERIES ###############
q_avg_load <- 'SELECT avg(val_0) FROM az_load_l'
q_avg_load_max <- 'SELECT max(val_0) FROM az_load_l'
q_avg_load_min <- 'SELECT min(val_0) FROM az_load_l'
q_az_load_val_0 <- 'SELECT val_0 FROM az_load_l'
q_az_load_val_0_gvt <- 'SELECT val_0, gvt FROM az_load_l'
q_energy_all = 'SELECT * FROM energy_l'
q_energy_load = 'SELECT val_0 FROM energy_l WHERE gvt=(SELECT gvt FROM az_load_l WHERE val_0 > 0)'
Sq_info_str = "SELECT count(val_0) FROM {} WHERE INSTR(info, 'substring') > 0" # or use the LIKE operator
############################## 1.1) AVG AZ LOAD #######################
data1 <- data.frame(
    AZs = azs,
    Load = result(q_avg_load),
    std = result_sd(q_az_load_val_0)
)
MAX<-max(data1$Load)
theme_set(theme_grey(base_size=6))
pdfName<-"1.1-Mean_Load_AZs.pdf"
p1 <- ggplot(data1) +
    geom_bar(aes(x=AZs, y=Load), stat="identity", fill="blue", alpha=0.9) +
    geom_errorbar(aes(x=AZs, ymin=Load-std, ymax=Load+std), width=0.4, colour="orange", alpha=0.9, size=1) +
    geom_hline(yintercept=MAX, color="red") +
    geom_text(aes(3, MAX, label=MAX, vjust = -1), size = 2)+
    ylim(NA,1)+
    labs(title="Availability Zones Mean Load",
         x ="Availability Zones", 
         y = "Load (Mean / Standard Deviation)")
ggsave(pdfName, p1, width = 4, height = 4, scale = 1)

############################## 1.2) MAX AZ LOAD #######################
data1 <- data.frame(
    AZs = azs,
    Load = result(q_avg_load_max)
)
MAX<-max(data1$Load)
pdfName<-"1.2-MAX_Load_AZs.pdf"
p2 <- ggplot(data1) +
    geom_bar(aes(x=AZs, y=Load), stat="identity", fill="blue", alpha=0.9)+
    geom_hline(yintercept=MAX, color="red") +
    geom_text(aes(3,MAX, label=MAX, vjust = -1), size = 2)+
    ylim(NA,1)+
    labs(title="Availability Zones Max Load",
         x ="Availability Zones",
         y = "Load (Maximum)")
ggsave(pdfName, p2, width = 4, height = 4, scale = 1)
############################## 1.3) LOAD AND ENERGY #######################
qdmin = "select energy_l.val_0 from energy_l inner join az_load_l on energy_l.gvt = az_load_l.gvt and az_load_l.val_0 < :x"
qdmid = "select energy_l.val_0 from energy_l inner join az_load_l on energy_l.gvt = az_load_l.gvt and (az_load_l.val_0 > :x and az_load_l.val_0 < :y)"
qdmax = "select energy_l.val_0 from energy_l inner join az_load_l on energy_l.gvt = az_load_l.gvt and az_load_l.val_0 > :x"
leg<-function(xmin, xmax, err, incr, has_boarders=FALSE){
    resp<-c()
    if (has_boarders == TRUE){
        resp<-c(xmin-err)
    }
    for (i in seq(xmin,xmax, incr)){
        l<-paste0(toString(i-err), toString("-"), toString(i+err))
        resp<-c(resp,l)
    }
    if (has_boarders == TRUE){resp<-c(resp,xmax+err)}
    return(resp)
}
#print(leg(0.1, 0.8, 0.02, 0.1, TRUE))
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
    plot_name <- paste0(toString("1.3-Load_Energy_AZ"), toString(i), toString(ERR), toString(INCR))
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
############################## 2.1) HISTOGRAM PLOT #######################
fun_histogram_each_az <- function(con_az, i){
    x <- dbGetQuery(con_az, q_az_load_val_0_gvt)
    dat <- data.frame(
        AZLoad=x$val_0,
        gvt=x$gvt
    )
    BREAKS<-20
    pdf_name1 <- paste0(toString("2.1-Hist_AZ"), toString(i), toString(".pdf"))
    p21 <- ggplot(dat, aes(dat$AZLoad))+
        geom_histogram(bins=BREAKS)+
        labs(title=paste0("Load Histogram AZ",toString(i)),
             x ="Load", 
             y = "Frequency")
    ggsave(pdf_name1, p21, width = 4, height = 4, scale = 1)
}
i<-1
for (az_con in az_con_list){
    print(i)
    fun_histogram_each_az(az_con, i)
    i<-i+1
}

############################## 2.2) CDF ###############################
fun_frequency <- function(con_az, i){
    wf = table(dbGetQuery(con_az, q_az_load_val_0))
    tf = as.data.frame(wf)
    maxFreq <- which.max(tf$Freq)
    MAX_xy <- tf[maxFreq,]
    MAXx <- levels(MAX_xy[1]$Var1)[maxFreq]
    MAXy <- MAX_xy$Freq
    lab_max <- paste0(toString("1ª (Load="),toString(MAXx),toString(", Freq="),toString(MAXy),toString(")"))
    
    
    #tf2 <- as.data.frame(tf[-c(maxFreq),-c(MAXy)])
    tf2 <- tf
    tf2[maxFreq,] <- 0
    maxFreq2 <- which.max(tf2$Freq)
    MAX_xy2 <- tf2[maxFreq2,]
    MAXx2 <- as.numeric(levels(MAX_xy2[1]$Var1)[maxFreq2])
    MAXy2 <- MAX_xy2$Freq
    lab_max2 <- paste0(toString("2ª (Load="),toString(MAXx2),toString(", Freq="),toString(MAXy2),toString(")"))
    
    pdf_freq <- paste0(toString("2.2-Frequency_AZ"), toString(i), toString(".pdf"))
    plt_freq <- ggplot(data=tf, aes(x=Var1, y=Freq, group = 1)) +
        #geom_point()+
        geom_line()+
        scale_x_discrete(breaks=seq(0.0, 1.0, 0.005)) +
        geom_hline(yintercept=MAXy, color="red") +
        geom_label(aes(MAXx, MAXy, label=lab_max, vjust = 0.0, hjust = 0.0), nudge_x = 12,  size = 4, colour = "red") +
        geom_hline(yintercept=MAXy2, color="blue") +
        geom_label(aes(MAXx2, MAXy2, label=lab_max2, vjust = 0, hjust = 0), nudge_x = 12, size = 4, colour = "blue") +
        #theme(axis.text.x=element_blank(), axis.ticks.x=element_blank()) +
        labs(title=paste0("Load Frequency AZ",toString(i)), x ="Load (%)",y ="Frequency")
    ggsave(pdf_freq, plt_freq, width = 9, height = 5, scale = 1)
}
i<-1
print("2.2) Frequency")
for (az_con in az_con_list){
    print(i)
    fun_frequency(az_con, i)
    i<-i+1
}

fun_ecdf_ggplot<-function(){
    x1<-dbGetQuery(con1, q_az_load_val_0_gvt)
    cdf1<-ecdf(x1$val_0)
    dat1 <- data.frame(
        Load1=x1$val_0,
        gvt1=x1$gvt
    )
    x2<-dbGetQuery(con2, q_az_load_val_0_gvt)
    cdf2<-ecdf(x2$val_0)
    dat2 <- data.frame(
        Load2=x2$val_0,
        gvt2=x2$gvt
    )
    x3<-dbGetQuery(con3, q_az_load_val_0_gvt)
    cdf3<-ecdf(x3$val_0)
    dat3 <- data.frame(
        Load3=x3$val_0,
        gvt3=x3$gvt
    )
    x4<-dbGetQuery(con4, q_az_load_val_0_gvt)
    cdf4<-ecdf(x4$val_0)
    dat4 <- data.frame(
        Load4=x4$val_0,
        gvt4=x4$gvt
    )
    x5<-dbGetQuery(con5, q_az_load_val_0_gvt)
    cdf5<-ecdf(x5$val_0)
    dat5 <- data.frame(
        Load5=x5$val_0,
        gvt5=x5$gvt
    )
    x6<-dbGetQuery(con6, q_az_load_val_0_gvt)
    cdf6<-ecdf(x6$val_0)
    dat6 <- data.frame(
        Load6=x6$val_0,
        gvt6=x6$gvt
    )
    
    df_global <- data.frame(
        #key =c("AZ1", "AZ2", "AZ3","AZ4","AZ5","AZ6"),
        key=c(
            rep("AZ1", nrow(x1)),
            rep("AZ2", nrow(x2)),
            rep("AZ3", nrow(x3)),
            rep("AZ4", nrow(x4)),
            rep("AZ5", nrow(x5)),
            rep("AZ6", nrow(x6))),
        value=c(
            x1$val_0,
            x2$val_0,
            x3$val_0,
            x4$val_0,
            x5$val_0,
            x6$val_0))
    cdff<-ggplot(df_global, aes(value, colour=key)) + 
        stat_ecdf(geo = "step")
    ggsave("2.2-CDF_All_AZs_ggplot.pdf", cdff, width = 9, height = 5, scale = 1)
}
#CDF: FUNCIONA MAS NÃO É GGPLOT
cdf_default<-function(){
    pdf_nameCDF <- paste0(toString("2.2-CDF_AZs_default"), toString(".pdf"))
    pdf(pdf_nameCDF, width=7, height=5)
    plot(cdf6, verticals=TRUE, do.points=FALSE, xlim=1.0)
    lot(cdf5, verticals=TRUE, do.points=FALSE, add=TRUE, col='red')
    plot(cdf4, verticals=TRUE, do.points=FALSE, add=TRUE, col='orange')
    plot(cdf3, verticals=TRUE, do.points=FALSE, add=TRUE, col='green')
    plot(cdf2, verticals=TRUE, do.points=FALSE, add=TRUE, col='pink')
    plot(cdf1, verticals=TRUE, do.points=FALSE, add=TRUE, col='blue')
    dev.off()
}

outroCDF<-function(){
    df_cdf1 <- data.frame(AZ1 = x1$val_0)
    df_cdf1 <- melt(df_cdf1)
    df_cdf1 <- ddply(df_cdf1, AZ1, transform, ecd=ecdf(value)(value))
    df_cdf2 <- data.frame(AZ2 = x2$val_0)
    #df_cdf2 <- melt(df_cdf2)
    #df_cdf2 <- ddply(df_cdf2, (.variables), transform, ecd=ecdf(value)(value))
    df_cdf3 <- data.frame(AZ3 = x3$val_0)
    #df_cdf3 <- melt(df_cdf3)
    #df_cdf3 <- ddply(df_cdf3, (.variable), transform, ecd=ecdf(value)(value))
    df_cdf4 <- data.frame(AZ4 = x4$val_0)
    #df_cdf4 <- melt(df_cdf4)
    #df_cdf4 <- ddply(df_cdf4, (.variable), transform, ecd=ecdf(value)(value))
    df_cdf5 <- data.frame(AZ5 = x5$val_0)
    #df_cdf5 <- melt(df_cdf5)
    #df_cdf5 <- ddply(df_cdf5, (.variable), transform, ecd=ecdf(value)(value))
    df_cdf6 <- data.frame(AZ6 = x6$val_0)
    #df_cdf6 <- melt(df_cdf6)
    #df_cdf6 <- ddply(df_cdf6, (.variable), transform, ecd=ecdf(value)(value))
    
    cdff <- ggplot() +
        stat_ecdf(data=df_cdf1, aes(x=value, colour=variable)) +
        stat_ecdf(data=df_cdf2, aes(x=value, colour=variable)) +
        stat_ecdf(data=df_cdf3, aes(x=value, colour=variable)) +
        stat_ecdf(data=df_cdf4, aes(x=value, colour=variable)) +
        stat_ecdf(data=df_cdf5, aes(x=value, colour=variable)) +
        stat_ecdf(data=df_cdf6, aes(x=value, colour=variable)) +
    #    scale_fill_manual("AZs") + #, values=c('red', 'darkgreen', 'blue', 'magenta', 'orange', 'black')) +
    #    theme(legend.position="right")+
        theme(legend.title=element_blank()) +
        labs(title="CDF - Cumulative Distribution Function",
             x ="Load",
             y = "CDF(x)",
             fill='AZs:' ) +
        xlim(0,1)
    ggsave("03-CDF_All_AZs.pdf", cdff, width = 9, height = 5, scale = 1)
}

############################## 2.3) RADAR / SPIDER ##################
#h_av <- c(0, 20, 40)        # em percentual de requisições
#cons <- c(0, 30, 40)        # quantidade de operações realizadas
#ener <- c(3000, 150, 450)   # em eficiencia/redução total
#load <- c(60, 75, 90)       # percentual medio de carga
#slav <- c(0, 3, 9)          # quantidade de rejeições

q_replic_attend = "SELECT count(ai) FROM replic_d"
q_replic_add_host = "SELECT count(ai) FROM replic_d WHERE abs(val_0) > 0"
q_replic_add_energy = "SELECT sum(energy_f - energy_0) FROM replic_d"
h_av <- c(   # em percentual de requisições atendidas
    0,
    20,
    40,
    40
)

q_cons = "SELECT count(val_0) FROM consol_d"
q_cons_false_pos = "select count(ai) from consol_d where val_0 = 0"
q_cons_migrations = "select sum(val_f) from consol_d where val_0 > 0"
cons <- c(   # quantidade de operações realizadas
    0, 
    30, 
    40,
    35
)

q_ener_cons = "SELECT sum(energy_0 - energy_f) FROM consol_d"
q_ener_ha = "SELECT sum(energy_0 - energy_f) FROM replic_d"
ener <- c(   # em eficiencia/redução total
    0, 
    150, 
    750,
    300
)

q_avg_load
load <- c(   # percentual medio de carga
    60,
    75,
    90,
    90
)

q_reject = "SELECT count(val_0) FROM reject_l"
slav <- c(   # quantidade de rejeições
    0,
    3, 
    9,
    11
)
data=as.data.frame(matrix( c(h_av,cons,ener,load,slav), ncol=5))
## Metrics:
colnames(data)=c("HA" , "Consolid", "Energy-Effic", "Load", "SLAV")
## Tests:
rownames(data)=c("EUCA", "CHAVE-MAX", "PLACE", "CHAVE-LOCKR") #paste("Test" , letters[1:3] , sep="-")
# To use the fmsb package, I have to add 2 lines to the dataframe: the max and min of each topic to show on the plot!
data=rbind(c(100, max(cons), max(ener), 100, max(slav)), # Max values in range
           c(0, 0, 0, 0, 0) , data)                     # Min values in range
data
par(mar=c(1,1,1,1))
# Plot 1: Default radar chart proposed by the library:
radarchart(data)

# Plot 2: Same plot with custom features
colors_border=c( rgb(0.0,0.0,0.9,0.9),
                 rgb(0.9,0.0,0.0,0.9),
                 rgb(0.9,0.9,0.0,0.9),
                 rgb(0.0,0.6,0.2,0.9) )
colors_in=c( rgb(0.0,0.0,0.9,0.4),
             rgb(0.9,0.0,0.0,0.4),
             rgb(0.9,0.9,0.0,0.4),
             rgb(0.0,0.6,0.2,0.4) )
line_type=c(1,2,3,4)
radarchart( data, axistype=1, 
            #custom polygon
            pcol=colors_border , pfcol=colors_in , plwd=line_type , plty=line_type,
            #custom the grid
            cglcol="grey", cglty=1, axislabcol="grey", caxislabels=seq(0,100,25), cglwd=1,
            #custom labels
            vlcex=1.2 
)
legend(x=0.9, y=0.5, legend = rownames(data[-c(1,2),]), 
       y.intersp=0.25, x.intersp=0.25, bty="n", pch=20 , 
       col=colors_border, text.col = "black", cex=1, pt.cex=5,
       title="Tests:")

# Plot3: If you remove the 2 first lines, the function compute the max and min of each variable with the available data:
radarchart( data[-c(1,2),]  , axistype=0 , maxmin=F,
            #custom polygon
            pcol=colors_border , pfcol=colors_in , plwd=line_type, plty=line_type,
            #custom the grid
            cglcol="grey", cglty=1, axislabcol="black", cglwd=0.8, 
            #custom labels
            vlcex=1.2 
)
legend(x=0.9, y=0.5, legend = rownames(data[-c(1,2),]), 
       y.intersp=0.25, x.intersp=0.25, bty="n", pch=20 , 
       col=colors_border, text.col = "black", cex=1, pt.cex=5,
       title="Tests:")

############################## 2.4) SNAPSHOTS ###############
############################## 2.5) TRIGGERS EACH ################
q_trigger = "SELECT count(val_0), gvt FROM consol_d"
q_trigger_energy = "SELECT ai, (energy_0 - energy_f) as Efficiency FROM consol_d"

fun_trigger_each<-function(con, i){
    tt <-dbGetQuery(con, q_trigger_energy)
    az <- paste0(toString("AZ"), toString(i))    
    df_trig1 <- data.frame(
        key=rep(az, nrow(tt)),
        Efficiency=tt$Efficiency,
        Trigger=tt$ai)

    pdf_trig <- paste0(toString("2.5-Trigger_consol_"), toString(az), toString(".pdf"))
    plt_trig1<-ggplot(data=df_trig1, aes(x=Trigger, y=Efficiency, colour=key)) + #, stat="identity", fill="blue", alpha=0.9) +
        geom_line()
    ggsave(pdf_trig, plt_trig1, width = 9, height = 5, scale = 1)
}
n<-1
for (con in az_con_list){
    fun_trigger_each(con, n)
    n<-n+1
}
############################## 2.6) TRIGGERS ALL ################
q_trigger = "SELECT count(val_0), gvt FROM consol_d"
q_trigger_energy = "SELECT ai, (energy_0 - energy_f) as Efficiency FROM consol_d"

t1 <-dbGetQuery(con1, q_trigger_energy)
t2 <-dbGetQuery(con2, q_trigger_energy)
t3 <-dbGetQuery(con3, q_trigger_energy)
t4 <-dbGetQuery(con4, q_trigger_energy)
t5 <-dbGetQuery(con5, q_trigger_energy)
t6 <-dbGetQuery(con6, q_trigger_energy)

df_trig <- data.frame(
    #key =c("AZ1", "AZ2", "AZ3","AZ4","AZ5","AZ6"),
    key=c(
        rep("AZ1", nrow(t1)),
        rep("AZ2", nrow(t2)),
        rep("AZ3", nrow(t3)),
        rep("AZ4", nrow(t4)),
        rep("AZ5", nrow(t5)),
        rep("AZ6", nrow(t6))),
    Efficiency=c(
        t1$Efficiency,
        t2$Efficiency,
        t3$Efficiency,
        t4$Efficiency,
        t5$Efficiency,
        t6$Efficiency),
    Trigger=c(
        t1$ai,
        t2$ai,
        t3$ai,
        t4$ai,
        t5$ai,
        t6$ai)
)

plt_trig<-ggplot(data=df_trig, aes(x=Trigger, y=Efficiency, colour=key)) + #, stat="identity", fill="blue", alpha=0.9) +
        geom_line() #+geom_point()
ggsave("2.6-Trigger_consol.pdf", plt_trig, width = 9, height = 5, scale = 1)

######################## DISCONNECT in main func ######################
dbDisconnect(con1)
dbDisconnect(con2)
dbDisconnect(con3)
dbDisconnect(con4)
dbDisconnect(con5)
dbDisconnect(con6)
#dbDisconnect(con7)

}

for (test in test_l){
    main(test)
} 

############################## 2.7) THEORETICAL (Numb. of AZs / Regions) ######

############################## 3.1) QUERY ENERGY #############################
query_energy = 'SELECT * FROM energy_l'
avg_energy1 <-dbGetQuery(con1, query_energy)
avg_energy2 <-dbGetQuery(con2, query_energy)
avg_energy3 <-dbGetQuery(con3, query_energy)
avg_energy4 <-dbGetQuery(con4, query_energy)
avg_energy5 <-dbGetQuery(con5, query_energy)
avg_energy6 <-dbGetQuery(con6, query_energy)

######################## ENERGY AZ1#####################################
data2 <- data.frame(
    Time <- avg_energy2$gvt,
    Energy <- avg_energy2$val_0
)
pdf("Energy2.pdf", width=7, height=5)
ggplot(data=data2, aes(x=Time, y=Energy), stat="identity", fill="blue", alpha=0.9) +
    geom_line()+
    geom_point()
dev.off()
######################## ENERGY AZ2#####################################
data2 <- data.frame(
    Time <- avg_energy2$gvt,
    Energy <- avg_energy2$val_0
)
pdf("Energy2.pdf", width=7, height=5)
ggplot(data=data2, aes(x=Time, y=Energy), stat="identity", fill="blue", alpha=0.9) +
    geom_line()+
    geom_point()
dev.off()
######################## ENERGY AZ3#####################################
data2 <- data.frame(
    Time <- avg_energy3$gvt,
    Energy <- avg_energy3$val_0
)
pdf("Energy3.pdf", width=7, height=5)
ggplot(data=data2, aes(x=Time, y=Energy), stat="identity", fill="blue", alpha=0.9) +
    geom_line()+
    geom_point()
dev.off()
######################## ENERGY AZ4#####################################
data2 <- data.frame(
    Time <- avg_energy4$gvt,
    Energy <- avg_energy4$val_0
)
pdf("Energy4.pdf", width=7, height=5)
ggplot(data=data2, aes(x=Time, y=Energy), stat="identity", fill="blue", alpha=0.9) +
    geom_line()+
    geom_point()
dev.off()
######################## ENERGY AZ5#####################################
data2 <- data.frame(
    Time <- avg_energy5$gvt,
    Energy <- avg_energy5$val_0
)
pdf("Energy5.pdf", width=7, height=5)
ggplot(data=data2, aes(x=Time, y=Energy), stat="identity", fill="blue", alpha=0.9) +
    geom_line()+
    geom_point()
dev.off()
######################## ENERGY AZ6#####################################
data2 <- data.frame(
    Time <- avg_energy6$gvt,
    Energy <- avg_energy6$val_0
)
pdf("Energy6.pdf", width=7, height=5)
ggplot(data=data2, aes(x=Time, y=Energy), stat="identity", fill="blue", alpha=0.9) +
    geom_line()+
    geom_point()
dev.off()

############################## 3.2) QUERY CONSOLIDA  #####################################################
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

############################## 3.3) ENERGY EFFICIENCY #### 
######################## DISCONNECT ######################
dbDisconnect(con1)
dbDisconnect(con2)
dbDisconnect(con3)
dbDisconnect(con4)
dbDisconnect(con5)
dbDisconnect(con6)
#dbDisconnect(con7)