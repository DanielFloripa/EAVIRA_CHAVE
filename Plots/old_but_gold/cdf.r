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