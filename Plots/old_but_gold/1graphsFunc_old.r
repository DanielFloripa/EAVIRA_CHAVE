library("rjson")


root <- "~/Dropbox/UDESC/Mestrado/Pratico/CHAVE-Sim/output/results/"
##################################################################
date <- paste0(toString(root), toString("18.05.29_04.21.42_"))
##################################################################

f_ff_cm <- paste0(toString(date), toString('CHAVE_max_FFD2I_1_20_False_False.json'))
f_tt_cm <- paste0(toString(date), toString('CHAVE_max_FFD2I_1_20_True_True.json'))
f_ft_cm <- paste0(toString(date), toString('CHAVE_max_FFD2I_1_20_False_True.json'))
f_tf_cm <- paste0(toString(date), toString('CHAVE_max_FFD2I_1_20_True_False.json'))

plotAll1<-function(f_ff, f_tt, f_ft, f_tf){
  # metrics <- "energy_acum_l" # "energy_l", 'energy_acum_l'
  pdfFile <- paste0(toString(date), toString('AZ1.pdf'))
  fileff <- fromJSON(file = f_ff)
  filett <- fromJSON(file = f_tt)
  fileft <- fromJSON(file = f_ft)
  filetf <- fromJSON(file = f_tf)
  az_ff <- fileff$AZ1$energy_acum_l
  az_tt <- filett$AZ1$energy_acum_l
  az_ft <- fileft$AZ1$energy_acum_l
  az_tf <- filetf$AZ1$energy_acum_l
  
  pdf(pdfFile,width=7,height=5)
  plot(az_ff, type="l", lwd=3, col="red", xlab="Time Unit", ylab="Energy (W)")
  par(new = TRUE)
  plot(az_tt, type="l", lwd=3, col="blue", lty=2, pch=2, axes = FALSE, xlab="", ylab="" )
  par(new = TRUE)
  plot(az_tf, type="l", lwd=3, col="green", lty=3, pch=3, axes = FALSE, xlab="", ylab="" )
  par(new = TRUE)
  plot(az_ft, type="l", lwd=3, col="magenta", lty=4, pch=4, axes = FALSE, xlab="", ylab="" )
  legend("topleft", lwd=3, legend=c("O:F+C:F", "O:T+C:T", "O:T+C:F", "O:F+C:T"),
         col=c("red", "blue", "green", "magenta"), lty=1:4, cex=0.8)
  dev.off()
}

plotAll2<-function(f_ff, f_tt, f_ft, f_tf){
  # metrics <- "energy_acum_l" # "energy_l"
  pdfFile <- paste0(toString(date), toString('AZ2.pdf'))
  fileff <- fromJSON(file = f_ff)
  filett <- fromJSON(file = f_tt)
  fileft <- fromJSON(file = f_ft)
  filetf <- fromJSON(file = f_tf)
  az_ff <- fileff$AZ2$energy_acum_l
  az_tt <- filett$AZ2$energy_acum_l
  az_ft <- fileft$AZ2$energy_acum_l
  az_tf <- filetf$AZ2$energy_acum_l
  
  pdf(pdfFile,width=7,height=5)
  plot(az_ff, type="l", lwd=3, col="red", xlab="Time Unit", ylab="Energy (W)")
  par(new = TRUE)
  plot(az_tt, type="l", lwd=3, col="blue", lty=2, pch=2, axes = FALSE, xlab="", ylab="" )
  par(new = TRUE)
  plot(az_tf, type="l", lwd=3, col="green", lty=3, pch=3, axes = FALSE, xlab="", ylab="" )
  par(new = TRUE)
  plot(az_ft, type="l", lwd=3, col="magenta", lty=4, pch=4, axes = FALSE, xlab="", ylab="" )
  legend("topleft", lwd=3, legend=c("O:F+C:F", "O:T+C:T", "O:T+C:F", "O:F+C:T"),
         col=c("red", "blue", "green", "magenta"), lty=1:4, cex=0.8)
  dev.off()
}

plotAll3<-function(f_ff, f_tt, f_ft, f_tf){
  # metrics <- "energy_acum_l" # "energy_l"
  pdfFile <- paste0(toString(date), toString('AZ3.pdf'))
  fileff <- fromJSON(file = f_ff)
  filett <- fromJSON(file = f_tt)
  fileft <- fromJSON(file = f_ft)
  filetf <- fromJSON(file = f_tf)
  az_ff <- fileff$AZ3$energy_acum_l
  az_tt <- filett$AZ3$energy_acum_l
  az_ft <- fileft$AZ3$energy_acum_l
  az_tf <- filetf$AZ3$energy_acum_l
  
  pdf(pdfFile,width=7,height=5)
  plot(az_ff, type="l", lwd=3, col="red", xlab="Time Unit", ylab="Energy (W)")
  par(new = TRUE)
  plot(az_tt, type="l", lwd=3, col="blue", lty=2, pch=2, axes = FALSE, xlab="", ylab="" )
  par(new = TRUE)
  plot(az_tf, type="l", lwd=3, col="green", lty=3, pch=3, axes = FALSE, xlab="", ylab="" )
  par(new = TRUE)
  plot(az_ft, type="l", lwd=3, col="magenta", lty=4, pch=4, axes = FALSE, xlab="", ylab="" )
  legend("topleft", lwd=3, legend=c("O:F+C:F", "O:T+C:T", "O:T+C:F", "O:F+C:T"),
         col=c("red", "blue", "green", "magenta"), lty=1:4, cex=0.8)
  dev.off()
}

plotAll4<-function(f_ff, f_tt, f_ft, f_tf, cols){
  # metrics <- "energy_acum_l" # "energy_l"
  pdfFile <- paste0(toString(date), toString('AZ4.pdf'))
  fileff <- fromJSON(file = f_ff)
  filett <- fromJSON(file = f_tt)
  fileft <- fromJSON(file = f_ft)
  filetf <- fromJSON(file = f_tf)
  az_ff <- fileff$AZ4$energy_acum_l
  az_tt <- filett$AZ4$energy_acum_l
  az_ft <- fileft$AZ4$energy_acum_l
  az_tf <- filetf$AZ4$energy_acum_l
  
  pdf(pdfFile,width=7,height=5)
  plot(az_ff, type="l", lwd=3, col="red", xlab="Time Unit", ylab="Energy (W)")
  par(new = TRUE)
  plot(az_tt, type="l", lwd=3, col="blue", lty=2, pch=2, axes = FALSE, xlab="", ylab="" )
  par(new = TRUE)
  plot(az_tf, type="l", lwd=3, col="green3", lty=3, pch=3, axes = FALSE, xlab="", ylab="" )
  par(new = TRUE)
  plot(az_ft, type="l", lwd=3, col="magenta", lty=4, pch=4, axes = FALSE, xlab="", ylab="" )
  legend("topleft", lwd=3, legend=c("O:F+C:F", "O:T+C:T", "O:T+C:F", "O:F+C:T"),
         col=c("red", "blue", "green", "magenta"), lty=1:4, cex=0.8)
  dev.off()
}

plotAll5<-function(f_ff, f_tt, f_ft, f_tf){
  # metrics <- "energy_acum_l" # "energy_l"
  pdfFile <- paste0(toString(date), toString('AZ5.pdf'))
  fileff <- fromJSON(file = f_ff)
  filett <- fromJSON(file = f_tt)
  fileft <- fromJSON(file = f_ft)
  filetf <- fromJSON(file = f_tf)
  az_ff <- fileff$AZ5$energy_acum_l
  az_tt <- filett$AZ5$energy_acum_l
  az_ft <- fileft$AZ5$energy_acum_l
  az_tf <- filetf$AZ5$energy_acum_l
  
  pdf(pdfFile,width=7,height=5)
  plot(az_ff, type="l", lwd=3, col="red", xlab="Time Unit", ylab="Energy (W)")
  par(new = TRUE)
  plot(az_tt, type="l", lwd=3, col="blue", lty=2, pch=2, axes = FALSE, xlab="", ylab="" )
  par(new = TRUE)
  plot(az_tf, type="l", lwd=3, col="green", lty=3, pch=3, axes = FALSE, xlab="", ylab="" )
  par(new = TRUE)
  plot(az_ft, type="l", lwd=3, col="magenta", lty=4, pch=4, axes = FALSE, xlab="", ylab="" )
  legend("topleft", lwd=3, legend=c("O:F+C:F", "O:T+C:T", "O:T+C:F", "O:F+C:T"),
         col=c("red", "blue", "green", "magenta"), lty=1:4, cex=0.8)
  dev.off()
}

plotAll6<-function(f_ff, f_tt, f_ft, f_tf){
  # metrics <- "energy_acum_l" # "energy_l"
  pdfFile <- paste0(toString(date), toString('AZ6.pdf'))
  fileff <- fromJSON(file = f_ff)
  filett <- fromJSON(file = f_tt)
  fileft <- fromJSON(file = f_ft)
  filetf <- fromJSON(file = f_tf)
  az_ff <- fileff$AZ6$energy_acum_l
  az_tt <- filett$AZ6$energy_acum_l
  az_ft <- fileft$AZ6$energy_acum_l
  az_tf <- filetf$AZ6$energy_acum_l
  
  pdf(pdfFile,width=7,height=5)
  plot(az_ff, type="l", lwd=3, col="red", xlab="Time Unit", ylab="Energy (W)")
  par(new = TRUE)
  plot(az_tt, type="l", lwd=3, col="blue", lty=2, pch=2, axes = FALSE, xlab="", ylab="" )
  par(new = TRUE)
  plot(az_tf, type="l", lwd=3, col="green", lty=3, pch=3, axes = FALSE, xlab="", ylab="" )
  par(new = TRUE)
  plot(az_ft, type="l", lwd=3, col="magenta", lty=4, pch=4, axes = FALSE, xlab="", ylab="" )
  legend("topleft", lwd=3, legend=c("O:F+C:F", "O:T+C:T", "O:T+C:F", "O:F+C:T"),
         col=c("red", "blue", "green", "magenta"), lty=1:4, cex=0.8)
  dev.off()
}


x1<-plotAll1(f_ff_cm, f_tt_cm, f_ft_cm, f_tf_cm)
x2<-plotAll2(f_ff_cm, f_tt_cm, f_ft_cm, f_tf_cm)
x3<-plotAll3(f_ff_cm, f_tt_cm, f_ft_cm, f_tf_cm)
x4<-plotAll4(f_ff_cm, f_tt_cm, f_ft_cm, f_tf_cm)
x5<-plotAll5(f_ff_cm, f_tt_cm, f_ft_cm, f_tf_cm)
x6<-plotAll6(f_ff_cm, f_tt_cm, f_ft_cm, f_tf_cm)
