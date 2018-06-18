
library("rjson")
file <- fromJSON(file = '/results/18.05.21_23.12.31_CHAVE_PlacementFirst_FFD2I_1_20_True_False')
#az4_ea <- as.data.frame(file$AZ4$energy_acum_l)
pl_az1_e <- file$AZ1$energy_l
plot(pl_az1_e, type="l", col="blue")
pl_az1_ea <- file$AZ1$energy_acum_l
plot(pl_az1_ea, type="l", col="red")

pl_az2_e <- file$AZ2$energy_l
plot(pl_az2_e, type="l", col="blue")
pl_az2_ea <- file$AZ2$energy_acum_l
plot(pl_az2_ea, type="l", col="red")

pl_az3_e <- file$AZ3$energy_l
plot(pl_az3_e, type="l", col="blue")
pl_az3_ea <- file$AZ3$energy_acum_l
plot(pl_az3_ea, type="l", col="red")

pl_az4_e <- file$AZ4$energy_l
plot(pl_az4_e, type="l", col="blue")
pl_az4_ea <- file$AZ4$energy_acum_l
plot(pl_az4_ea, type="l", col="red")

pl_az5_e <- file$AZ5$energy_l
plot(pl_az5_e, type="l", col="blue")
pl_az5_ea <- file$AZ5$energy_acum_l
plot(pl_az5_ea, type="l", col="red")

pl_az6_e <- file$AZ6$energy_l
plot(pl_az6_e, type="l", col="blue")
pl_az6_ea <- file$AZ6$energy_acum_l
plot(pl_az6_ea, type="l", col="red")

plot(c(pl_az1_ea, pl_az2_ea, pl_az3_ea, pl_az4_ea, pl_az5_ea, pl_az6_ea), type="l", col="red")

