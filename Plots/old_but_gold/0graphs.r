#install.packages(c("data.tree", "jsonlite", "magrittr", "curl" )) 
# or devtools::install_github("gluc/data.tree")
#install.packages(c("rjson"))
#install.packages(c("reshape2"))
#install.packages(c("ggplot2"))
#install.packages(c("jsonlite"))

# pdf("SampleGraph.pdf",width=7,height=5)
#library(reshape2)
#library(ggplot2)
install.packages("jqr")
library("jqr")
library("rjson")
file <- fromJSON(file = '/home/daniel/Dropbox/UDESC/Mestrado/Pratico/CHAVE-Sim/results/18.05.20_19.25.47_CHAVE_PlacementFirst_FFD2I_1_20_False_False.json')

az1_eff <- file$"AZ1"$"energy_l"
plot(az1_eff, type="l", col="blue", xlab="Time Unit", ylab="Energy (W)")
az1_eaff<- file$"AZ1"$"energy_acum_l"
plot(az1_eaff, type="l", col="red", xlab="Time Unit", ylab="Energy (W)")

az2_eff <- file$AZ2$energy_l
plot(az2_eff, type="l", col="blue", xlab="Time Unit", ylab="Energy (W)")
az2_eaff<- file$AZ2$energy_acum_l
plot(az2_eaff, type="l", col="red", xlab="Time Unit", ylab="Energy (W)")

az3_eff <- file$AZ3$energy_l
plot(az3_eff, type="l", col="blue", xlab="Time Unit", ylab="Energy (W)")
az3_eaff<- file$AZ3$energy_acum_l
plot(az3_eaff, type="l", col="red", xlab="Time Unit", ylab="Energy (W)")

az4_eff <- file$AZ4$energy_l
plot(az4_eff, type="l", col="blue", xlab="Time Unit", ylab="Energy (W)")
az4_eaff<- file$AZ4$energy_acum_l
plot(az4_eaff, type="l", col="red", xlab="Time Unit", ylab="Energy (W)")

az5_eff <- file$AZ5$energy_l
plot(az5_eff, type="l", col="blue", xlab="Time Unit", ylab="Energy (W)")
az5_eaff<- file$AZ5$energy_acum_l
plot(az5_eaff, type="l", col="red", xlab="Time Unit", ylab="Energy (W)")

az6_eff <- file$AZ6$energy_l
plot(az6_eff, type="l", col="blue", xlab="Time Unit", ylab="Energy (W)")
az6_eaff<- file$AZ6$energy_acum_l
plot(az6_eaff, type="l", col="red", xlab="Time Unit", ylab="Energy (W)")


filett <- fromJSON(file = '/home/daniel/Dropbox/UDESC/Mestrado/Pratico/CHAVE-Sim/results/18.05.20_19.25.47_CHAVE_PlacementFirst_FFD2I_1_20_True_True.json')
#az4_eaff<- as.data.frame(file$AZ4$energy_acum_l)

az1_ett <- filett$AZ1$energy_l
plot(az1_ett, type="l", col="blue", xlab="Time Unit", ylab="Energy (W)")
az1_eatt <- filett$AZ1$energy_acum_l
plot(az1_eatt, type="l", col="red", xlab="Time Unit", ylab="Energy (W)")

az2_ett <- filett$AZ2$energy_l
plot(az2_ett, type="l", col="blue", xlab="Time Unit", ylab="Energy (W)")
az2_eatt <- filett$AZ2$energy_acum_l
plot(az2_eatt, type="l", col="red", xlab="Time Unit", ylab="Energy (W)")

az3_ett <- filett$AZ3$energy_l
plot(az3_ett, type="l", col="blue", xlab="Time Unit", ylab="Energy (W)")
az3_eatt <- filett$AZ3$energy_acum_l
plot(az3_eatt, type="l", col="red", xlab="Time Unit", ylab="Energy (W)")

az4_ett <- filett$AZ4$energy_l
plot(az4_ett, type="l", col="blue", xlab="Time Unit", ylab="Energy (W)")
az4_eatt <- filett$AZ4$energy_acum_l
plot(az4_eatt, type="l", col="red", xlab="Time Unit", ylab="Energy (W)")

az5_ett <- filett$AZ5$energy_l
plot(az5_ett, type="l", col="blue", xlab="Time Unit", ylab="Energy (W)")
az5_eatt <- filett$AZ5$energy_acum_l
plot(az5_eatt, type="l", col="red", xlab="Time Unit", ylab="Energy (W)")

az6_ett <- filett$AZ6$energy_l
plot(az6_ett, type="l", col="blue", xlab="Time Unit", ylab="Energy (W)")
az6_eatt <- filett$AZ6$energy_acum_l
plot(az6_eatt, type="l", col="red", xlab="Time Unit", ylab="Energy (W)")




filetf <- fromJSON(file = '/home/daniel/Dropbox/UDESC/Mestrado/Pratico/CHAVE-Sim/results/18.05.20_19.25.47_CHAVE_PlacementFirst_FFD2I_1_20_True_False.json')

az1_etf <- filetf$AZ1$energy_l
plot(az1_etf, type="l", col="blue", xlab="Time Unit", ylab="Energy (W)")
az1_eatf <- filetf$AZ1$energy_acum_l
plot(az1_eatf, type="l", col="red", xlab="Time Unit", ylab="Energy (W)")

az2_etf <- filetf$AZ2$energy_l
plot(az2_etf, type="l", col="blue", xlab="Time Unit", ylab="Energy (W)")
az2_eatf <- filetf$AZ2$energy_acum_l
plot(az2_eatf, type="l", col="red", xlab="Time Unit", ylab="Energy (W)")

az3_etf <- filetf$AZ3$energy_l
plot(az3_etf, type="l", col="blue", xlab="Time Unit", ylab="Energy (W)")
az3_eatf <- filetf$AZ3$energy_acum_l
plot(az3_eatf, type="l", col="red", xlab="Time Unit", ylab="Energy (W)")

az4_etf <- filetf$AZ4$energy_l
plot(az4_etf, type="l", col="blue", xlab="Time Unit", ylab="Energy (W)")
az4_eatf <- filetf$AZ4$energy_acum_l
plot(az4_eatf, type="l", col="red", xlab="Time Unit", ylab="Energy (W)")

az5_etf <- filetf$AZ5$energy_l
plot(az5_etf, type="l", col="blue", xlab="Time Unit", ylab="Energy (W)")
az5_eatf <- filetf$AZ5$energy_acum_l
plot(az5_eatf, type="l", col="red", xlab="Time Unit", ylab="Energy (W)")

az6_etf <- filetf$AZ6$energy_l
plot(az6_etf, type="l", col="blue", xlab="Time Unit", ylab="Energy (W)")
az6_eatf <- filetf$AZ6$energy_acum_l
plot(az6_eatf, type="l", col="red", xlab="Time Unit", ylab="Energy (W)")


fileft <- fromJSON(file = '/home/daniel/Dropbox/UDESC/Mestrado/Pratico/CHAVE-Sim/results/18.05.20_19.25.47_CHAVE_PlacementFirst_FFD2I_1_20_False_True.json')

az1_eft <- fileft$AZ1$energy_l
plot(az1_eft, type="l", col="blue", xlab="Time Unit", ylab="Energy (W)")
az1_eaft <- fileft$AZ1$energy_acum_l
plot(az1_eaft, type="l", col="red", xlab="Time Unit", ylab="Energy (W)")

az2_eft <- fileft$AZ2$energy_l
plot(az2_eft, type="l", col="blue", xlab="Time Unit", ylab="Energy (W)")
az2_eaft <- fileft$AZ2$energy_acum_l
plot(az2_eaft, type="l", col="red", xlab="Time Unit", ylab="Energy (W)")

az3_eft <- fileft$AZ3$energy_l
plot(az3_eft, type="l", col="blue", xlab="Time Unit", ylab="Energy (W)")
az3_eaft <- fileft$AZ3$energy_acum_l
plot(az3_eaft, type="l", col="red", xlab="Time Unit", ylab="Energy (W)")

az4_eft <- fileft$AZ4$energy_l
plot(az4_eft, type="l", col="blue", xlab="Time Unit", ylab="Energy (W)")
az4_eaft <- fileft$AZ4$energy_acum_l
plot(az4_eaft, type="l", col="red", xlab="Time Unit", ylab="Energy (W)")

az5_eft <- fileft$AZ5$energy_l
plot(az5_eft, type="l", col="blue", xlab="Time Unit", ylab="Energy (W)")
az5_eaft <- fileft$AZ5$energy_acum_l
plot(az5_eaft, type="l", col="red", xlab="Time Unit", ylab="Energy (W)")

az6_eft <- fileft$AZ6$energy_l
plot(az6_eft, type="l", col="blue", xlab="Time Unit", ylab="Energy (W)")
az6_eaft <- fileft$AZ6$energy_acum_l
plot(az6_eaft, type="l", col="red", xlab="Time Unit", ylab="Energy (W)")





plot(az1_eaff, type="l", col="red", xlab="Time Unit", ylab="Energy (W)")
par(new = TRUE)
plot(az1_eatt, type="l", col="blue", axes = FALSE, xlab="", ylab="" )
par(new = TRUE)
plot(az1_eatf, type="l", col="green", axes = FALSE, xlab="", ylab="" )
par(new = TRUE)
plot(az1_eaft, type="l", col="yellow", axes = FALSE, xlab="", ylab="" )

plot(az2_eaff, type="l", col="red", xlab="Time Unit", ylab="Energy (W)")
par(new = TRUE)
plot(az2_eatt, type="l", col="blue", axes = FALSE, xlab="", ylab="" )
par(new = TRUE)
plot(az2_eatf, type="l", col="green", axes = FALSE, xlab="", ylab="" )
par(new = TRUE)
plot(az2_eaft, type="l", col="yellow", axes = FALSE, xlab="", ylab="" )

plot(az3_eaff, type="l", col="red", xlab="Time Unit", ylab="Energy (W)")
par(new = TRUE)
plot(az3_eatt, type="l", col="blue", axes = FALSE, xlab="", ylab="" )
par(new = TRUE)
plot(az3_eatf, type="l", col="green", axes = FALSE, xlab="", ylab="" )
par(new = TRUE)
plot(az3_eaft, type="l", col="yellow", axes = FALSE, xlab="", ylab="" )

plot(az4_eaff, type="l", col="red", xlab="Time Unit", ylab="Energy (W)")
par(new = TRUE)
plot(az4_eatt, type="l", col="blue", axes = FALSE, xlab="", ylab="" )
par(new = TRUE)
plot(az4_eatf, type="l", col="green", axes = FALSE, xlab="", ylab="" )
par(new = TRUE)
plot(az4_eaft, type="l", col="yellow", axes = FALSE, xlab="", ylab="" )

pdf("SampleGraph.pdf",width=7,height=5)
plot(az5_eaff, type="l", col="red", xlab="Time Unit", ylab="Energy (W)")
par(new = TRUE)
plot(az5_eatt, type="l", col="blue", axes = FALSE, xlab="", ylab="" )
par(new = TRUE)
plot(az5_eatf, type="l", col="green", axes = FALSE, xlab="", ylab="" )
par(new = TRUE)
plot(az5_eaft, type="l", col="yellow", axes = FALSE, xlab="", ylab="" )
legend("topleft", legend=c("O:F+C:F", "O:T+C:T", "O:T+C:F", "O:F+C:T"),
       col=c("red", "blue", "green", "yellow"), lty=1:4, cex=0.8)
dev.off()


pdf("AZ6_EnergyAccumulated.pdf",width=7,height=5)
plot(fileft$AZ6$energy_l, type="l", col="red", xlab="Time Unit", ylab="Energy (W)")
par(new = TRUE)
plot(az6_eatt, type="l", col="blue", lty=2, axes = FALSE, xlab="", ylab="" )
par(new = TRUE)
plot(az6_eatf, type="l", col="green", lty=3, axes = FALSE, xlab="", ylab="" )
par(new = TRUE)
plot(az6_eaft, type="l", col="yellow", lty=4, axes = FALSE, xlab="", ylab="" )
legend("topleft", legend=c("O:F+C:F", "O:T+C:T", "O:T+C:F", "O:F+C:T"),
       col=c("red", "blue", "green", "yellow"), lty=1:4, cex=0.8)
dev.off()




######################################################################################



root <- "~/Dropbox/UDESC/Mestrado/Pratico/CHAVE-Sim/output/results/"
##################################################################
date <- paste0(toString(root), toString("18.05.29_04.21.42_"))
##################################################################
pdfFile <- paste0(toString(date), toString('AZ1.pdf'))

f_ff_cm <- paste0(toString(date), toString('CHAVE_max_FFD2I_1_20_False_False.json'))
f_tt_cm <- paste0(toString(date), toString('CHAVE_max_FFD2I_1_20_True_True.json'))
f_ft_cm <- paste0(toString(date), toString('CHAVE_max_FFD2I_1_20_False_True.json'))
f_tf_cm <- paste0(toString(date), toString('CHAVE_max_FFD2I_1_20_True_False.json'))

x1<-plotAll1(f_ff_cm, f_tt_cm, f_ft_cm, f_tf_cm)
x2<-plotAll2(f_ff_cm, f_tt_cm, f_ft_cm, f_tf_cm)
x3<-plotAll3(f_ff_cm, f_tt_cm, f_ft_cm, f_tf_cm)
x4<-plotAll4(f_ff_cm, f_tt_cm, f_ft_cm, f_tf_cm)
x5<-plotAll5(f_ff_cm, f_tt_cm, f_ft_cm, f_tf_cm)
x6<-plotAll6(f_ff_cm, f_tt_cm, f_ft_cm, f_tf_cm)

##########################################################################################
fileff_cm <- fromJSON(file = f_ff_cm)
filett_cm <- fromJSON(file = f_tt_cm)
fileft_cm <- fromJSON(file = f_ft_cm)
filetf_cm <- fromJSON(file = f_tf_cm)
##########################################################################################
f_ff_cl <- paste0(toString(date), toString('CHAVE_lock_FFD2I_1_20_False_False.json'))
f_tt_cl <- paste0(toString(root), toString('CHAVE_lock_FFD2I_1_20_True_True.json'))
f_ft_cl <- paste0(toString(root), toString('CHAVE_lock_FFD2I_1_20_False_True.json'))
f_tf_cl <- paste0(toString(root), toString('CHAVE_lock_FFD2I_1_20_True_False.json'))
fileff_cl <- fromJSON(file = f_ff_cl)
filett_cl <- fromJSON(file = f_tt_cl)
fileft_cl <- fromJSON(file = f_ft_cl)
filetf_cl <- fromJSON(file = f_tf_cl)
#################################################################################
f_ff_em <- paste0(toString(date), toString('EUCA_max_FFD2I_1_20_False_False.json'))
f_tf_em <- paste0(toString(root), toString('EUCA_max_FFD2I_1_20_True_False.json'))
fileff_em <- fromJSON(file = f_ff_em)
filetf_em <- fromJSON(file = f_tf_em)
#################################################################################
az <- "AZ1"
pdfFile <- paste0(toString(root), toString('plots/'),  toString(az), toString(context))
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
plot(az_ft, type="l", lwd=3, col="yellow", lty=4, pch=4, axes = FALSE, xlab="", ylab="" )
legend("topleft", lwd=3, legend=c("O:F+C:F", "O:T+C:T", "O:T+C:F", "O:F+C:T"),
       col=c("red", "blue", "green", "yellow"), lty=1:4, cex=0.8)
dev.off()

az <- "AZ2"
pdfFile <- paste0(toString(root), toString('plots/'),  toString(az), toString(context))
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
plot(az_ft, type="l", lwd=3, col="yellow", lty=4, pch=4, axes = FALSE, xlab="", ylab="" )
legend("topleft", lwd=3, legend=c("O:F+C:F", "O:T+C:T", "O:T+C:F", "O:F+C:T"),
       col=c("red", "blue", "green", "yellow"), lty=1:4, cex=0.8)
dev.off()

az <- "AZ3"
pdfFile <- paste0(toString(root), toString('plots/'),  toString(az), toString(context))
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
plot(az_ft, type="l", lwd=3, col="yellow", lty=4, pch=4, axes = FALSE, xlab="", ylab="" )
legend("topleft", lwd=3, legend=c("O:F+C:F", "O:T+C:T", "O:T+C:F", "O:F+C:T"),
       col=c("red", "blue", "green", "yellow"), lty=1:4, cex=0.8)
dev.off()

az <- "AZ4"
pdfFile <- paste0(toString(root), toString('plots/'),  toString(az), toString(context))
az_ff <- fileff$AZ4$energy_acum_l
az_tt <- filett$AZ4$energy_acum_l
az_ft <- fileft$AZ4$energy_acum_l
az_tf <- filetf$AZ4$energy_acum_l
pdf(pdfFile,width=7,height=5)
plot(az_ff, type="l", lwd=3, col="red", xlab="Time Unit", ylab="Energy (W)")
par(new = TRUE)
plot(az_tt, type="l", lwd=3, col="blue", lty=2, pch=2, axes = FALSE, xlab="", ylab="" )
par(new = TRUE)
plot(az_tf, type="l", lwd=3, col="green", lty=3, pch=3, axes = FALSE, xlab="", ylab="" )
par(new = TRUE)
plot(az_ft, type="l", lwd=3, col="yellow", lty=4, pch=4, axes = FALSE, xlab="", ylab="" )
legend("topleft", lwd=3, legend=c("O:F+C:F", "O:T+C:T", "O:T+C:F", "O:F+C:T"),
       col=c("red", "blue", "green", "yellow"), lty=1:4, cex=0.8)
dev.off()

az <- "AZ5"
pdfFile <- paste0(toString(root), toString('plots/'),  toString(az), toString(context))
az_ff <- fileff$AZ5$energy_acum_l
az_tt <- filett$AZ5$energy_acum_l
az_ft <- fileft$AZ5$energy_acum_l
az_tf <- filetf$AZ5$energy_acum_l
pdf(pdfFile,width=7,height=5)
plot(az_ff, type="l", lwd=3, col="red", xlab="Time Unit", ylab="Energy (W)")
par(new = TRUE)
plot(az_tt, type="l", lwd=3, lwd=3, col="blue", lty=2, pch=2, axes = FALSE, xlab="", ylab="" )
par(new = TRUE)
plot(az_tf, type="l", lwd=3, col="green", lty=3, pch=3, axes = FALSE, xlab="", ylab="" )
par(new = TRUE)
plot(az_ft, type="l", lwd=3, col="yellow", lty=4, pch=4, axes = FALSE, xlab="", ylab="" )
legend("topleft", lwd=3, legend=c("O:F+C:F", "O:T+C:T", "O:T+C:F", "O:F+C:T"),
       col=c("red", "blue", "green", "yellow"), lty=1:4, cex=0.8)
dev.off()

az <- "AZ6"
pdfFile <- paste0(toString(root), toString('plots/'),  toString(az), toString(context))
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
plot(az_ft, type="l", lwd=3, col="yellow", lty=4, pch=4, axes = FALSE, xlab="", ylab="" )
legend("topleft", lwd=3, legend=c("O:F+C:F", "O:T+C:T", "O:T+C:F", "O:F+C:T"),
       col=c("red", "blue", "green", "yellow"), lty=1:4, cex=0.8)
dev.off()

