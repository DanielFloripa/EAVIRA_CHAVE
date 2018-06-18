#install.packages(c("data.tree", "jsonlite", "magrittr", "curl" )) # or devtools::install_github("gluc/data.tree")

install.packages(c("rjson"))
library("rjson")
file <- fromJSON(file = '/home/debian/Dropbox/UDESC/Mestrado/Pratico/CHAVE-Sim/results/18.05.22_00.40.22_CHAVE_PlacementFirst_FFD2I_1_20_True_True.json')
#az4_ea <- as.data.frame(file$AZ4$energy_acum_l)
pl_az1_e <- file$AZ1$energy_l
plot(pl_az1_e, type="l", col="blue", xlab="Time Unit", ylab="Energy (W)")
pl_az1_ea <- file$AZ1$energy_acum_l
plot(pl_az1_ea, type="l", col="red", xlab="Time Unit", ylab="Energy (W)")
box()

pl_az2_e <- file$AZ2$energy_l
plot(pl_az2_e, type="l", col="blue", xlab="Time Unit", ylab="Energy (W)")
pl_az2_ea <- file$AZ2$energy_acum_l
plot(pl_az2_ea, type="l", col="red", xlab="Time Unit", ylab="Energy (W)")

pl_az3_e <- file$AZ3$energy_l
plot(pl_az3_e, type="l", col="blue", xlab="Time Unit", ylab="Energy (W)")
pl_az3_ea <- file$AZ3$energy_acum_l
plot(pl_az3_ea, type="l", col="red", xlab="Time Unit", ylab="Energy (W)")

pl_az4_e <- file$AZ4$energy_l
plot(pl_az4_e, type="l", col="blue", xlab="Time Unit", ylab="Energy (W)")
pl_az4_ea <- file$AZ4$energy_acum_l
plot(pl_az4_ea, type="l", col="red", xlab="Time Unit", ylab="Energy (W)")

pl_az5_e <- file$AZ5$energy_l
plot(pl_az5_e, type="l", col="blue", xlab="Time Unit", ylab="Energy (W)")
pl_az5_ea <- file$AZ5$energy_acum_l
plot(pl_az5_ea, type="l", col="red", xlab="Time Unit", ylab="Energy (W)")

pl_az6_e <- file$AZ6$energy_l
plot(pl_az6_e, type="l", col="blue", xlab="Time Unit", ylab="Energy (W)")
pl_az6_ea <- file$AZ6$energy_acum_l
plot(pl_az6_ea, type="l", col="red", xlab="Time Unit", ylab="Energy (W)")

filetf <- fromJSON(file = '/home/debian/Dropbox/UDESC/Mestrado/Pratico/CHAVE-Sim/results/18.05.22_00.40.22_CHAVE_PlacementFirst_FFD2I_1_20_True_False.json')
#az4_ea <- as.data.frame(file$AZ4$energy_acum_l)

plot(filetf$AZ1$energy_l, type="l", col="blue", xlab="Time Unit", ylab="Energy (W)")
plot(filetf$AZ1$energy_acum_l, type="l", col="red", xlab="Time Unit", ylab="Energy (W)")
box()

pl_az2_e <- file$AZ2$energy_l
plot(pl_az2_e, type="l", col="blue", xlab="Time Unit", ylab="Energy (W)")
pl_az2_ea <- file$AZ2$energy_acum_l
plot(pl_az2_ea, type="l", col="red", xlab="Time Unit", ylab="Energy (W)")

pl_az3_e <- file$AZ3$energy_l
plot(pl_az3_e, type="l", col="blue", xlab="Time Unit", ylab="Energy (W)")
pl_az3_ea <- file$AZ3$energy_acum_l
plot(pl_az3_ea, type="l", col="red", xlab="Time Unit", ylab="Energy (W)")

pl_az4_e <- file$AZ4$energy_l
plot(pl_az4_e, type="l", col="blue", xlab="Time Unit", ylab="Energy (W)")
pl_az4_ea <- file$AZ4$energy_acum_l
plot(pl_az4_ea, type="l", col="red", xlab="Time Unit", ylab="Energy (W)")

pl_az5_e <- file$AZ5$energy_l
plot(pl_az5_e, type="l", col="blue", xlab="Time Unit", ylab="Energy (W)")
pl_az5_ea <- file$AZ5$energy_acum_l
plot(pl_az5_ea, type="l", col="red", xlab="Time Unit", ylab="Energy (W)")

pl_az6_e <- file$AZ6$energy_l
plot(pl_az6_e, type="l", col="blue", xlab="Time Unit", ylab="Energy (W)")
pl_az6_ea <- file$AZ6$energy_acum_l
plot(pl_az6_ea, type="l", col="red", xlab="Time Unit", ylab="Energy (W)")

