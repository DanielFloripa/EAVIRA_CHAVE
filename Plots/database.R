#!/usr/bin/env Rscript
###############################################
#### This R is part of CHAVE-SIM Project    ###
#### Avalable at dscar.ga/chave             ###
###############################################
############################## 0.0) LIBRARIES AND PACKAGES ####
#install.packages(c("RSQLite", "ggplot2", "fmsb", "dplyr"),repos = "http://cran.us.r-project.org", quiet=TRUE)
library("dplyr", quietly=TRUE)
library("fmsb", quietly=TRUE)
library("ggplot2", quietly=TRUE)
library("DBI", quietly=TRUE)
############################## 0.1) MAIN PARAMETERS AND DIRS #################################
# Get the parameter:
path = commandArgs(trailingOnly=TRUE)

if(length(path) == 0 ){
  date = "18.07.22-21.41.45/"
  #pwd <- "/home/daniel/output/"
  #pwd <- "/media/debian/"
  pwd <- "~/Dropbox/UDESC/Mestrado/Pratico/CHAVE-Sim/output/"
  rdef <- paste0(toString(pwd), toString(date), toString("results/"))
} else{
  rdef <- paste0(toString(path), toString("results/"))
}
#test <- "EUCA_CF_L:None_O:False_C:False_R:False/"
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
            "CHAVE_CF_L:None_O:False_C:False_R:True")

main<-function(test){
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
      #testFiles(f)
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
  ############################## 11) AVG AZ LOAD #######################
  data1 <- data.frame(
      AZs = azs,
      Load = result(q_avg_load),
      std = result_sd(q_az_load_val_0)
  )
  MAX<-max(data1$Load)
  theme_set(theme_grey(base_size=6))
  pdfName<-"11-Mean_Load_AZs.pdf"
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
  
  ############################## 12) MAX AZ LOAD #######################
  data1 <- data.frame(
      AZs = azs,
      Load = result(q_avg_load_max)
  )
  MAX<-max(data1$Load)
  pdfName<-"12-MAX_Load_AZs.pdf"
  p2 <- ggplot(data1) +
      geom_bar(aes(x=AZs, y=Load), stat="identity", fill="blue", alpha=0.9)+
      geom_hline(yintercept=MAX, color="red") +
      geom_text(aes(3,MAX, label=MAX, vjust = -1), size = 2)+
      ylim(NA,1)+
      labs(title="Availability Zones Max Load",
           x ="Availability Zones",
           y = "Load (Maximum)")
  ggsave(pdfName, p2, width = 4, height = 4, scale = 1)
  ############################## 13) LOAD AND ENERGY #######################
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
      plot_name <- paste0(toString("13-Load_Energy_AZ"), toString(i), toString(ERR), toString(INCR))
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
  ############################## 21) HISTOGRAM AZ_LOAD #######################
  fun_histogram_each_az <- function(con_az, i){
      x <- dbGetQuery(con_az, q_az_load_val_0_gvt)
      dat <- data.frame(
          AZLoad=x$val_0,
          gvt=x$gvt
      )
      BREAKS<-20
      pdf_name1 <- paste0(toString("21-Hist_AZ"), toString(i), toString(".pdf"))
      p21 <- ggplot(dat, aes(dat$AZLoad))+
          geom_histogram(bins=BREAKS)+
          labs(title=paste0("Load Histogram AZ",toString(i)),
               x ="Load", 
               y = "Frequency")
      ggsave(pdf_name1, p21, width = 4, height = 4, scale = 1)
  }
  print("Running (21) HISTOGRAM")
  i<-1
  for (az_con in az_con_list){
      print(i)
      fun_histogram_each_az(az_con, i)
      i<-i+1
  }
  ############################## 22) Probability Frequency az_load ###############################
  # i<-6; con_az<-con6
  load_objectives <-c()
  i<-1
  print("Running (22) Prob Frequency")
  for (con_az in az_con_list){
      print(i)
      norm <- function(x){
          return(round((x/sum(x)), digits = 3))
      }
      just<-function(x){
          if(x > 50){
              return(1)
          }
          return(-1)
      }
      wf <- table(dbGetQuery(con_az, q_az_load_val_0))
      tf <- as.data.frame(wf)
      tf<- tf %>% mutate(Freq = norm(Freq),
                         #Var1 = as.numeric(as.character(Var1)))
                         Var1 = round(as.numeric(as.character(Var1))*100, digits = 3))
  
      maxFreq <- which.max(tf$Freq)
      MAX_xy <- tf[maxFreq,]
      MAXx <- MAX_xy$Var1
      MAXy <- MAX_xy$Freq
      lab_max <- paste0(toString("1ª -> P("),toString(MAXy),toString(") de carga em "),toString(MAXx),toString("%"))
      
      #tf2 <- as.data.frame(tf[-c(maxFreq),-c(MAXy)])
      tf2 <- tf
      tf2[maxFreq,] <- 0
      maxFreq2 <- which.max(tf2$Freq)
      MAX_xy2 <- tf2[maxFreq2,]
      MAXx2 <- MAX_xy2$Var1
      MAXy2 <- MAX_xy2$Freq
      lab_max2 <- paste0(toString("2ª -> P("),toString(MAXy2),toString(") de carga em "),toString(MAXx2),toString("%"))
      
      tf3 <- tf2
      tf3[maxFreq2,] <- 0
      maxFreq3 <- which.max(tf3$Freq)
      MAX_xy3 <- tf3[maxFreq3,]
      MAXx3 <- MAX_xy3$Var1
      MAXy3 <- MAX_xy3$Freq
      lab_max3 <- paste0(toString("3ª -> P("),toString(MAXy3),toString(") de carga em "),toString(MAXx3),toString("%"))
      
      load_objectives <-c(load_objectives, MAXx, MAXx2, MAXx3)
      cols=c("red", "blue", "magenta")
      fcols=c("white", "white", "white")
      pch=c(21, 22, 23)
      lty=c(1, 2, 4)
      hjust=c(just(MAXx), just(MAXx2),just(MAXx3))
      vjust=c(0,1,-0.3)
  
      pdf_freq <- paste0(toString("22-Frequency_AZ"), toString(i), toString(".pdf"))
      plt_freq <- ggplot(data=tf, aes(x=Var1, y=Freq, group = 1, ymax=0.2, xmax=100)) +
          geom_line()+
          geom_point(size=0.7)+
          #
          geom_hline(yintercept=MAXy, color=cols[1], lty=lty[1], size=1) +
          geom_hline(yintercept=MAXy2, color=cols[2], lty=lty[2], size=1) +
          geom_hline(yintercept=MAXy3, color=cols[3], lty=lty[3], size=1) +
          #
          geom_label(aes(MAXx, MAXy, label=lab_max, vjust = vjust[1], hjust = hjust[1]), nudge_x = 1,  size = 4, colour = cols[1]) +
          geom_label(aes(MAXx2, MAXy2, label=lab_max2, vjust = vjust[2], hjust = hjust[2]), nudge_x = 1, size = 4, colour = cols[2]) +
          geom_label(aes(MAXx3, MAXy3, label=lab_max3, vjust = vjust[3], hjust = hjust[3]), nudge_x = 1, size = 4, colour = cols[3]) +
          #
          geom_point(aes(MAXx, MAXy), size=3, color=cols[1], pch=pch[1], fill=fcols[1])+
          geom_point(aes(MAXx2, MAXy2), size=3, color=cols[2], pch=pch[2], fill=fcols[2])+
          geom_point(aes(MAXx3, MAXy3), size=3, color=cols[3], pch=pch[3], fill=fcols[3])+
          #theme(axis.text.x=element_blank(), axis.ticks.x=element_blank()) +
          labs(title=paste0("Probabilidade de ocorrência de cargas na AZ",toString(i)), x ="Carga (%)",y ="Probabilidade (0~1)")
      ggsave(pdf_freq, plt_freq, width = 9, height = 5, scale = 1)
      i<-i+1
  }
  
  outro_fun_frequency2<-function(){
      ggplot(diamonds, aes(price, stat(density), colour = cut)) +
          geom_freqpoly(binwidth = 500)
  }
  outr_fun_todo<-function(){
      dfMAX<-data.frame(
          cMAXx=c(MAXx, MAXx2, MAXx3),
          cMAXy=c(MAXy, MAXy2, MAXy3),
          clab_max=c(lab_max,lab_max2,lab_max3),
          cols=c("red", "blue", "magenta"),
          fcols=c("black", "black", "black"),
          pch=c(21, 22, 23),
          lty=c(1, 2, 4),
          hjust=c(just(MAXx), just(MAXx2),just(MAXx3)),
          vjust=c(0,1,0)
      )
      geom_hline(data=dfMAX, aes(yintercept=cMAXy, color=cols)) +
          #
          geom_label(data=dfMAX, aes(x=cMAXx, y=cMAXy, label=clab_max, vjust = vjust, hjust = hjust, colour = cols), nudge_x = 1,  size = 4) +
          #
          geom_point(data=dfMAX, aes(x=cMAXx, y=cMAXy, color=cols, pch=pch, fill=fcols), size=3)
  }
  outro_ecdf_ggplot<-function(){
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
  outro_cdf_default<-function(){
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
  outro_CDF<-function(){
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
  
  ############################## 23) RADAR / SPIDER ##################
  #print("In the next file databaseRadar.R")
  #source(databaseRadar.R, local = TRUE)
  ############################## 24) SNAPSHOTS ###############
  ############################## 25) TRIGGERS EACH ################
  q_trigger = "SELECT count(val_0), gvt FROM consol_d"
  q_trigger_energy = "SELECT ai, (energy_0 - energy_f) as Efficiency FROM consol_d"
  
  fun_trigger_each<-function(con, i){
      if(test == "EUCA_CF_L:None_O:False_C:False_R:False" ||
         test == "CHAVE_CF_L:None_O:False_C:False_R:False" ||
         test == "CHAVE_CF_L:None_O:False_C:False_R:True"){
        return(0)
      }
      tt <-dbGetQuery(con, q_trigger_energy)
      az <- paste0(toString("AZ"), toString(i))    
      df_trig1 <- data.frame(
          key=rep(az, nrow(tt)),
          Efficiency=tt$Efficiency,
          Trigger=tt$ai)
  
      pdf_trig <- paste0(toString("25-Trigger_consol_"), toString(az), toString(".pdf"))
      plt_trig1<-ggplot(data=df_trig1, aes(x=Trigger, y=Efficiency, colour=key)) + #, stat="identity", fill="blue", alpha=0.9) +
          geom_line()
      ggsave(pdf_trig, plt_trig1, width = 9, height = 5, scale = 1)
  }
  n<-1
  #for (con in az_con_list){
  #    fun_trigger_each(con, n)
  #    n<-n+1
  #}
  ############################## 26) TRIGGERS HISTOGRAM EACH ################
  q_trigger = "SELECT count(val_0), gvt FROM consol_d"
  q_trigger_energy = "SELECT ai, (1-(energy_f/energy_0))*100 as Efficiency FROM consol_d" # where energy_0-energy_f > 1"
  i=1;con=con1
  fun_trigger_histogram<-function(con, i){
      if(test == "EUCA_CF_L:None_O:False_C:False_R:False" ||
         test == "CHAVE_CF_L:None_O:False_C:False_R:False" ||
         test == "CHAVE_CF_L:None_O:False_C:False_R:True"){
        return(0)
      }
      az <- paste0(toString("AZ"), toString(i))
      pdf_trig <- function(x){
          return(paste0(toString("26-Trigger_"), toString(az), toString(x), toString(".pdf")))
      }
      qq <-dbGetQuery(con, q_trigger_energy)
      MEAN = mean(qq$Efficiency)
      # Histograma  frequencia
      freq_hist<-function(){
          df1 <- as.data.frame(qq)
          base<-ggplot(df1, aes(x=Efficiency))+
              stat_bin(binwidth = 1, col="red")+
              labs(title=paste0("Redução de energia na consolidação para AZ",toString(i)), 
                   x = "Percentual de redução de energia (%)", 
                   y = "Freqência (bin=1)")
          ggsave(pdf_trig("_stat_bin_"), base, width = 9, height = 5, scale = 1)
      }
      #
      # Lolipop
      lolipop<-function(){
          x= df1$ai #seq(0, 2*pi, length.out=100)
          data=data.frame(x=x, y=df1$Efficiency)
          data=data %>% mutate(mycolor = ifelse(y>0, "blue", "red"))
          loli<-ggplot(data, aes(x=x, y=y)) +
              geom_segment( aes(x=x, xend=x, y=0, yend=y, color=mycolor), size=1.3, alpha=0.9) +
              geom_point(color="black", size=1)+
              theme_light() + theme(legend.position = "none", panel.border = element_blank()) +
              xlab("Trigger") + ylab("Redução (%)")
          ggsave(pdf_trig("_loli_"), loli, width = 9, height = 5, scale = 1)
      }
      #
      levs <- c(seq(from=0, to=100, by=5))
      cond <- tryCatch({
         wf <- table(cut(qq$Efficiency, levs, right = FALSE))
      },
      error=function(cond){
        message("ERROR")
      },
      warning=function(cond){
        message("WARNING")
      },
      finnaly={
        print("OK!")
      })
      #wf <- table(cut(qq$Efficiency, levs, right = FALSE))
      df <- as.data.frame(wf)
      df<- df %>% mutate(Var1 = c(seq(from=5, to=100, by=5)))
      plt_trig1<-ggplot(data=df, aes(x=Freq, y=Var1)) + #, stat="identity", fill="blue", alpha=0.9) +
          geom_bar(stat="identity")+
          #geom_hline(yintercept=MEAN, color="red") +
          #geom_text(aes(100, MEAN, label=MEAN, vjust = -1), size = 5)+
          labs(title=paste0("Trigger Histogram AZ",toString(i)), x ="Triggers", y = "Redução de consumo (%)")
      ggsave(pdf_trig("_Histogr_"), plt_trig1, width = 9, height = 5, scale = 1)
  }
  n<-1
  print("Running: 26) fun_trigger_histogram()")
  for (con in az_con_list){
      fun_trigger_histogram(con, n)
      n<-n+1
  }
  ############################## 2.7) TRIGGERS ALL ################
  fun_trigger_line_all<-function(){
      if(test == "EUCA_CF_L:None_O:False_C:False_R:False" ||
         test == "CHAVE_CF_L:None_O:False_C:False_R:False" ||
         test == "CHAVE_CF_L:None_O:False_C:False_R:True"){
        return(0)
      }
      q_trigger = "SELECT count(val_0), gvt FROM consol_d"
      q_trigger_energy = "SELECT ai, (1-(energy_f/energy_0))*100 as Efficiency FROM consol_d"
      
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
  
      plt_trig<-ggplot(data=df_trig, aes(x=Efficiency, colour=key)) + #, stat="identity", fill="blue", alpha=0.9) +
          geom_freqpoly(binwidth = 5)+
          labs(title="Percentual de redução de energia na consolidação", 
               x = "% de redução de energia", 
               y = "Freqência (bin=5)")
      plt_trig
      ggsave("27-Trigger_consol_ALL.pdf", plt_trig, width = 9, height = 5, scale = 1)
  }
  print("Running: 27) trigger_line_all")
  fun_trigger_line_all()
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
    print(paste0(toString("Running: "), toString(test)))
    main(test)
} 
 #quit()
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