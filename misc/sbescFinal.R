## Global Settings
par(mfrow = c(1,1))
library(gplots)

# Data center data
#VI NIT 1000 PR 0.1
VI_MBFD_MM_0.1K <- read.table("../resultados/vpc-m3_g5k_0.1_VI_NORMAL_BF_MBDF_MM.dat", header = T, sep =" ")
VI_MBFD_EAVIRA_0.1K <- read.table("../resultados/vpc-m3_g5k_0.1_VI_NORMAL_BF_MBDF_EAVIRA.dat", header = T, sep =" ")
VI_VITREEM_EAVIRA_0.1K <- read.table("../resultados/vpc-m3_g5k_0.1_VI_NORMAL_BF_VITREEM_EAVIRA.dat", header = T, sep =" ")
VI_VITREEM_MM_0.1K <- read.table("../resultados/vpc-m3_g5k_0.1_VI_NORMAL_BF_VITREEM_MM.dat", header = T, sep =" ")
#VI Nodes 1000 0.1
header <- c ("NIT","get_id","get_used_ram","get_used_storage","get_used_cpu","get_cpu_usage","get_energy_consumption","get_wasted_energy")
VI_MBFD_EAVIRA_DC_nodes <- read.table("../resultados/vpc-m3_g5k_0.1_VI_NORMAL_BF_MBDF_EAVIRA_datacenter_nodes_status.dat", sep =" ")
colnames(VI_MBFD_EAVIRA_DC_nodes) <- unlist (header)
VI_MBFD_MM_DC_nodes <- read.table("../resultados/vpc-m3_g5k_0.1_VI_NORMAL_BF_MBDF_MM_datacenter_nodes_status.dat", sep =" ")
colnames(VI_MBFD_MM_DC_nodes) <- unlist (header)
VI_VITREEM_EAVIRA_DC_nodes <- read.table("../resultados/vpc-m3_g5k_0.1_VI_NORMAL_BF_VITREEM_EAVIRA_datacenter_nodes_status.dat", sep =" ")
colnames(VI_VITREEM_EAVIRA_DC_nodes) <- unlist (header)
VI_VITREEM_MM_DC_nodes <- read.table("../resultados/vpc-m3_g5k_0.1_VI_NORMAL_BF_VITREEM_MM_datacenter_nodes_status.dat", sep =" ")
colnames(VI_VITREEM_MM_DC_nodes) <- unlist (header)
#VI Net 1000 0.1
header <- c ("NIT","conection","load")
VI_MBFD_EAVIRA_DC_net <- read.table("../resultados/vpc-m3_g5k_0.1_VI_NORMAL_BF_MBDF_EAVIRA_datacenter_network_status.dat", sep =" ")
colnames(VI_MBFD_EAVIRA_DC_net) <- unlist (header)
VI_MBFD_MM_DC_net <- read.table("../resultados/vpc-m3_g5k_0.1_VI_NORMAL_BF_MBDF_MM_datacenter_network_status.dat", sep =" ")
colnames(VI_MBFD_MM_DC_net) <- unlist (header)
VI_VITREEM_EAVIRA_DC_net <- read.table("../resultados/vpc-m3_g5k_0.1_VI_NORMAL_BF_VITREEM_EAVIRA_datacenter_network_status.dat", sep =" ")
colnames(VI_VITREEM_EAVIRA_DC_net) <- unlist (header)
VI_VITREEM_MM_DC_net <- read.table("../resultados/vpc-m3_g5k_0.1_VI_NORMAL_BF_VITREEM_MM_datacenter_network_status.dat", sep =" ")
colnames(VI_VITREEM_MM_DC_net) <- unlist (header)

mycolors1 = c("lightblue", "mistyrose", "lightcyan", "lightyellow")
sbescLeg = c ("MBFD_EAVIRA","MBFD_MM","VITREEM_EAVIRA","VITREEM_MM")

# ************************************************* #
# Done
pdf ("01-AAR_VI_0-1.pdf")


AAR_VI_MBFD_EAVIRA <- (100*sum(VI_MBFD_EAVIRA_0.1K[,5]))/(max(VI_MBFD_EAVIRA_0.1K[,12]))
AAR_VI_MBFD_MM <- (100*sum(VI_MBFD_MM_0.1K[,5]))/(max(VI_MBFD_MM_0.1K[,12]))
AAR_VI_VITREEM_EAVIRA <- (100*sum(VI_VITREEM_EAVIRA_0.1K[,5]))/(max(VI_VITREEM_EAVIRA_0.1K[,12]))
AAR_VI_VITREEM_MM <- (100*sum(VI_VITREEM_MM_0.1K[,5]))/(max(VI_VITREEM_MM_0.1K[,12]))

AAR <- matrix (c (
	AAR_VI_MBFD_EAVIRA, AAR_VI_MBFD_MM, AAR_VI_VITREEM_EAVIRA, AAR_VI_VITREEM_MM), nr =4)

bp <- barplot2(AAR, beside = TRUE, plot.grid = TRUE, ylim = c(0,100), ylab = "(%)", space = 1,
	names.arg = sbescLeg,
	col = mycolors1,
	)
dev.off()

# ************************************************* #
# Breaks and Migration table
# Done
Breaks2 <- matrix ( c("SumAllocations","Sum_Breaks","Allocation/Break","Breaks/Allocation",
    sum (VI_MBFD_EAVIRA_0.1K[,5]),
    sum (VI_MBFD_EAVIRA_0.1K[,10]),
    sum (VI_MBFD_EAVIRA_0.1K[,5])/sum(VI_MBFD_EAVIRA_0.1K[,10]),    
    sum (VI_MBFD_EAVIRA_0.1K[,10])/sum(VI_MBFD_EAVIRA_0.1K[,5]),        
    sum (VI_MBFD_MM_0.1K[,5]),
    sum (VI_MBFD_MM_0.1K[,10]),
    sum (VI_MBFD_MM_0.1K[,5])/sum(VI_MBFD_MM_0.1K[,10]),
    sum (VI_MBFD_MM_0.1K[,10])/sum(VI_MBFD_MM_0.1K[,5]),    
    sum (VI_VITREEM_EAVIRA_0.1K[,5]),
    sum (VI_VITREEM_EAVIRA_0.1K[,10]),
    sum (VI_VITREEM_EAVIRA_0.1K[,5])/sum(VI_VITREEM_EAVIRA_0.1K[,10]),
    sum (VI_VITREEM_EAVIRA_0.1K[,10])/sum(VI_VITREEM_EAVIRA_0.1K[,5]),    
    sum (VI_VITREEM_MM_0.1K[,5]),
    sum (VI_VITREEM_MM_0.1K[,10]),
    sum (VI_VITREEM_MM_0.1K[,5])/sum(VI_VITREEM_MM_0.1K[,10]),
    sum (VI_VITREEM_MM_0.1K[,10])/sum(VI_VITREEM_MM_0.1K[,5])    
    ), nc =5 )
headerSm <- c("","MBFD_EAVIRA","MBFD_MM","VITREEM_EAVIRA","VITREEM_MM")
colnames(Breaks2) <- unlist (headerSm)

Migrations <- matrix ( c("SumAllocations","SumMigrations","Migrations/Allocations","Allocation/Migrations",
    sum (VI_MBFD_EAVIRA_0.1K[,5]),
    max (VI_MBFD_EAVIRA_0.1K[,13]),
    max (VI_MBFD_EAVIRA_0.1K[,13])/sum (VI_MBFD_EAVIRA_0.1K[,5]),
	sum (VI_MBFD_EAVIRA_0.1K[,5])/max (VI_MBFD_EAVIRA_0.1K[,13]),	
    sum (VI_MBFD_MM_0.1K[,5]),
    max (VI_MBFD_MM_0.1K[,13]),
    max (VI_MBFD_MM_0.1K[,13])/sum (VI_MBFD_MM_0.1K[,5]),    
    sum (VI_MBFD_MM_0.1K[,5])/max (VI_MBFD_MM_0.1K[,13]),
    sum (VI_VITREEM_EAVIRA_0.1K[,5]),
    max (VI_VITREEM_EAVIRA_0.1K[,13]),
	max(VI_VITREEM_EAVIRA_0.1K[,13])/sum (VI_VITREEM_EAVIRA_0.1K[,5]),
	sum (VI_VITREEM_EAVIRA_0.1K[,5])/max(VI_VITREEM_EAVIRA_0.1K[,13]),	
    sum (VI_VITREEM_MM_0.1K[,5]),
    max (VI_VITREEM_MM_0.1K[,13]),
    max (VI_VITREEM_MM_0.1K[,13])/sum (VI_VITREEM_MM_0.1K[,5]),
    sum (VI_VITREEM_MM_0.1K[,5])/max (VI_VITREEM_MM_0.1K[,13]) 
    ), nc =5 )
headerSm <- c("","MBFD_EAVIRA","MBFD_MM","VITREEM_EAVIRA","VITREEM_MM")
colnames(Migrations) <- unlist (headerSm)

# ************************************************* #
# Done!

pdf ("01-Power.pdf")

Power <- matrix ( c(
	mean(sapply(VI_MBFD_EAVIRA_0.1K[,8], function(y) { if (y == 0) NA else y }), na.rm = TRUE),
	mean(sapply(VI_MBFD_EAVIRA_0.1K[,9], function(y) { if (y == 0) NA else y }), na.rm = TRUE),	
	mean(sapply(VI_MBFD_MM_0.1K[,8], function(y) { if (y == 0) NA else y }), na.rm = TRUE),
	mean(sapply(VI_MBFD_MM_0.1K[,9], function(y) { if (y == 0) NA else y }), na.rm = TRUE),	
	mean(sapply(VI_VITREEM_EAVIRA_0.1K[,8], function(y) { if (y == 0) NA else y }), na.rm = TRUE),
	mean(sapply(VI_VITREEM_EAVIRA_0.1K[,9], function(y) { if (y == 0) NA else y }), na.rm = TRUE),	
	mean(sapply(VI_VITREEM_MM_0.1K[,8], function(y) { if (y == 0) NA else y }), na.rm = TRUE),
	mean(sapply(VI_VITREEM_MM_0.1K[,9], function(y) { if (y == 0) NA else y }), na.rm = TRUE)), nc =4 )
headerSm <- c("MBFD_EAVIRA","MBFD_MM","VITREEM_EAVIRA","VITREEM_MM")
colnames(Power) <- unlist (headerSm)

PowerSD <- matrix ( c(
	sd(sapply(VI_MBFD_EAVIRA_0.1K[,8], function(y) { if (y == 0) NA else y }), na.rm = TRUE),
	sd(sapply(VI_MBFD_EAVIRA_0.1K[,9], function(y) { if (y == 0) NA else y }), na.rm = TRUE),
	sd(sapply(VI_MBFD_MM_0.1K[,8], function(y) { if (y == 0) NA else y }), na.rm = TRUE),
	sd(sapply(VI_MBFD_MM_0.1K[,9], function(y) { if (y == 0) NA else y }), na.rm = TRUE),
	sd(sapply(VI_VITREEM_EAVIRA_0.1K[,8], function(y) { if (y == 0) NA else y }), na.rm = TRUE),
	sd(sapply(VI_VITREEM_EAVIRA_0.1K[,9], function(y) { if (y == 0) NA else y }), na.rm = TRUE),	
	sd(sapply(VI_VITREEM_MM_0.1K[,8], function(y) { if (y == 0) NA else y }), na.rm = TRUE),
	sd(sapply(VI_VITREEM_MM_0.1K[,9], function(y) { if (y == 0) NA else y }), na.rm = TRUE)), nc =4 )
headerSm <- c("MBFD_EAVIRA","MBFD_MM","VITREEM_EAVIRA","VITREEM_MM")
colnames(PowerSD) <- unlist (headerSm)
upper = Power+ PowerSD
lower = Power- PowerSD

bp <- barplot2(Power, beside = TRUE, plot.grid = TRUE, plot.ci = TRUE, ci.u = upper, ci.l = lower, 
	legend = c("Provider's fraction","Total power"), ylim = c(0,25000),
    col = c("aquamarine","lightgreen"), ylab = "watts"#, main = c("Data center energy consumption")
    )
dev.off()

# # ************************************************* #
pdf ("01_CPU.pdf")

# Nro de host no DC = 106
# DC e homogeneo!
# file ivrealloc/input/physical/g5k.dat
# CPUs por host = 24
# MEM por host = 256
# Sto por host = 1024 
# net por host = 1000
# DCresources = #CPU, #MEM, #STO, #NET
DCresources = c(2544,27136,108544,106000)

### CPU usage 
VI_MBFD_MM_DC_nodes_CPU <- matrix (VI_MBFD_MM_DC_nodes[,6], nc = 1000)
sumVI_MBFD_MM_DC_nodes_CPU <- 0 
for (i in 1:1000) { sumVI_MBFD_MM_DC_nodes_CPU[i] = sum (VI_MBFD_MM_DC_nodes_CPU[,i]) }
U_VI_MBFD_MM_DC_nodes_CPU <- (100*(mean(sapply(sumVI_MBFD_MM_DC_nodes_CPU, function(y) { if (y == 0) NA else y }), na.rm = TRUE))/DCresources[1])
U_VI_MBFD_MM_DC_nodes_CPUsd <- (100*(sd(sapply(sumVI_MBFD_MM_DC_nodes_CPU, function(y) { if (y == 0) NA else y }), na.rm = TRUE))/DCresources[1])

VI_MBFD_EAVIRA_DC_nodes_CPU <- matrix (VI_MBFD_EAVIRA_DC_nodes[,6], nc = 1000)
sumVI_MBFD_EAVIRA_DC_nodes_CPU <- 0 
for (i in 1:1000) { sumVI_MBFD_EAVIRA_DC_nodes_CPU[i] = sum (VI_MBFD_EAVIRA_DC_nodes_CPU[,i]) }
U_VI_MBFD_EAVIRA_DC_nodes_CPU <- (100*(mean(sapply(sumVI_MBFD_EAVIRA_DC_nodes_CPU, function(y) { if (y == 0) NA else y }), na.rm = TRUE))/DCresources[1])
U_VI_MBFD_EAVIRA_DC_nodes_CPUsd <- (100*(sd(sapply(sumVI_MBFD_EAVIRA_DC_nodes_CPU, function(y) { if (y == 0) NA else y }), na.rm = TRUE))/DCresources[1])

VI_VITREEM_MM_DC_nodes_CPU <- matrix (VI_VITREEM_MM_DC_nodes[,6], nc = 1000)
sumVI_VITREEM_MM_DC_nodes_CPU <- 0 
for (i in 1:1000) { sumVI_VITREEM_MM_DC_nodes_CPU[i] = sum (VI_VITREEM_MM_DC_nodes_CPU[,i]) }
U_VI_VITREEM_MM_DC_nodes_CPU <- (100*(mean(sapply(sumVI_VITREEM_MM_DC_nodes_CPU, function(y) { if (y == 0) NA else y }), na.rm = TRUE))/DCresources[1])
U_VI_VITREEM_MM_DC_nodes_CPUsd <- (100*(sd(sapply(sumVI_VITREEM_MM_DC_nodes_CPU, function(y) { if (y == 0) NA else y }), na.rm = TRUE))/DCresources[1])

VI_VITREEM_EAVIRA_DC_nodes_CPU <- matrix (VI_VITREEM_EAVIRA_DC_nodes[,6], nc = 1000)
sumVI_VITREEM_EAVIRA_DC_nodes_CPU <- 0 
for (i in 1:1000) { sumVI_VITREEM_EAVIRA_DC_nodes_CPU[i] = sum (VI_VITREEM_EAVIRA_DC_nodes_CPU[,i]) }
U_VI_VITREEM_EAVIRA_DC_nodes_CPU <- (100*(mean(sapply(sumVI_VITREEM_EAVIRA_DC_nodes_CPU, function(y) { if (y == 0) NA else y }), na.rm = TRUE))/DCresources[1])
U_VI_VITREEM_EAVIRA_DC_nodes_CPUsd <- (100*(sd(sapply(sumVI_VITREEM_EAVIRA_DC_nodes_CPU, function(y) { if (y == 0) NA else y }), na.rm = TRUE))/DCresources[1])

### MEM usage 
VI_MBFD_MM_DC_nodes_MEM <- matrix (VI_MBFD_MM_DC_nodes[,3], nc = 1000)
sumVI_MBFD_MM_DC_nodes_MEM <- 0 
for (i in 1:1000) { sumVI_MBFD_MM_DC_nodes_MEM[i] = sum (VI_MBFD_MM_DC_nodes_MEM[,i]) }
U_VI_MBFD_MM_DC_nodes_MEM <- (100*(mean(sapply(sumVI_MBFD_MM_DC_nodes_MEM, function(y) { if (y == 0) NA else y }), na.rm = TRUE))/DCresources[2])
U_VI_MBFD_MM_DC_nodes_MEMsd <- (100*(sd(sapply(sumVI_MBFD_MM_DC_nodes_MEM, function(y) { if (y == 0) NA else y }), na.rm = TRUE))/DCresources[2])

VI_MBFD_EAVIRA_DC_nodes_MEM <- matrix (VI_MBFD_EAVIRA_DC_nodes[,3], nc = 1000)
sumVI_MBFD_EAVIRA_DC_nodes_MEM <- 0 
for (i in 1:1000) { sumVI_MBFD_EAVIRA_DC_nodes_MEM[i] = sum (VI_MBFD_EAVIRA_DC_nodes_MEM[,i]) }
U_VI_MBFD_EAVIRA_DC_nodes_MEM <- (100*(mean(sapply(sumVI_MBFD_EAVIRA_DC_nodes_MEM, function(y) { if (y == 0) NA else y }), na.rm = TRUE))/DCresources[2])
U_VI_MBFD_EAVIRA_DC_nodes_MEMsd <- (100*(sd(sapply(sumVI_MBFD_EAVIRA_DC_nodes_MEM, function(y) { if (y == 0) NA else y }), na.rm = TRUE))/DCresources[2])

VI_VITREEM_MM_DC_nodes_MEM <- matrix (VI_VITREEM_MM_DC_nodes[,3], nc = 1000)
sumVI_VITREEM_MM_DC_nodes_MEM <- 0 
for (i in 1:1000) { sumVI_VITREEM_MM_DC_nodes_MEM[i] = sum (VI_VITREEM_MM_DC_nodes_MEM[,i]) }
U_VI_VITREEM_MM_DC_nodes_MEM <- (100*(mean(sapply(sumVI_VITREEM_MM_DC_nodes_MEM, function(y) { if (y == 0) NA else y }), na.rm = TRUE))/DCresources[2])
U_VI_VITREEM_MM_DC_nodes_MEMsd <- (100*(sd(sapply(sumVI_VITREEM_MM_DC_nodes_MEM, function(y) { if (y == 0) NA else y }), na.rm = TRUE))/DCresources[2])

VI_VITREEM_EAVIRA_DC_nodes_MEM <- matrix (VI_VITREEM_EAVIRA_DC_nodes[,3], nc = 1000)
sumVI_VITREEM_EAVIRA_DC_nodes_MEM <- 0 
for (i in 1:1000) { sumVI_VITREEM_EAVIRA_DC_nodes_MEM[i] = sum (VI_VITREEM_EAVIRA_DC_nodes_MEM[,i]) }
U_VI_VITREEM_EAVIRA_DC_nodes_MEM <- (100*(mean(sapply(sumVI_VITREEM_EAVIRA_DC_nodes_MEM, function(y) { if (y == 0) NA else y }), na.rm = TRUE))/DCresources[2])
U_VI_VITREEM_EAVIRA_DC_nodes_MEMsd <- (100*(sd(sapply(sumVI_VITREEM_EAVIRA_DC_nodes_MEM, function(y) { if (y == 0) NA else y }), na.rm = TRUE))/DCresources[2])

### Sto usage 
VI_MBFD_MM_DC_nodes_STO <- matrix (VI_MBFD_MM_DC_nodes[,4], nc = 1000)
sumVI_MBFD_MM_DC_nodes_STO <- 0 
for (i in 1:1000) { sumVI_MBFD_MM_DC_nodes_STO[i] = sum (VI_MBFD_MM_DC_nodes_STO[,i]) }
U_VI_MBFD_MM_DC_nodes_STO <- (100*(mean(sapply(sumVI_MBFD_MM_DC_nodes_STO, function(y) { if (y == 0) NA else y }), na.rm = TRUE))/DCresources[3])
U_VI_MBFD_MM_DC_nodes_STOsd <- (100*(sd(sapply(sumVI_MBFD_MM_DC_nodes_STO, function(y) { if (y == 0) NA else y }), na.rm = TRUE))/DCresources[3])

VI_MBFD_EAVIRA_DC_nodes_STO <- matrix (VI_MBFD_EAVIRA_DC_nodes[,4], nc = 1000)
sumVI_MBFD_EAVIRA_DC_nodes_STO <- 0 
for (i in 1:1000) { sumVI_MBFD_EAVIRA_DC_nodes_STO[i] = sum (VI_MBFD_EAVIRA_DC_nodes_STO[,i]) }
U_VI_MBFD_EAVIRA_DC_nodes_STO <- (100*(mean(sapply(sumVI_MBFD_EAVIRA_DC_nodes_STO, function(y) { if (y == 0) NA else y }), na.rm = TRUE))/DCresources[3])
U_VI_MBFD_EAVIRA_DC_nodes_STOsd <- (100*(sd(sapply(sumVI_MBFD_EAVIRA_DC_nodes_STO, function(y) { if (y == 0) NA else y }), na.rm = TRUE))/DCresources[3])

VI_VITREEM_MM_DC_nodes_STO <- matrix (VI_VITREEM_MM_DC_nodes[,4], nc = 1000)
sumVI_VITREEM_MM_DC_nodes_STO <- 0 
for (i in 1:1000) { sumVI_VITREEM_MM_DC_nodes_STO[i] = sum (VI_VITREEM_MM_DC_nodes_STO[,i]) }
U_VI_VITREEM_MM_DC_nodes_STO <- (100*(mean(sapply(sumVI_VITREEM_MM_DC_nodes_STO, function(y) { if (y == 0) NA else y }), na.rm = TRUE))/DCresources[3])
U_VI_VITREEM_MM_DC_nodes_STOsd <- (100*(sd(sapply(sumVI_VITREEM_MM_DC_nodes_STO, function(y) { if (y == 0) NA else y }), na.rm = TRUE))/DCresources[3])

VI_VITREEM_EAVIRA_DC_nodes_STO <- matrix (VI_VITREEM_EAVIRA_DC_nodes[,4], nc = 1000)
sumVI_VITREEM_EAVIRA_DC_nodes_STO <- 0 
for (i in 1:1000) { sumVI_VITREEM_EAVIRA_DC_nodes_STO[i] = sum (VI_VITREEM_EAVIRA_DC_nodes_STO[,i]) }
U_VI_VITREEM_EAVIRA_DC_nodes_STO <- (100*(mean(sapply(sumVI_VITREEM_EAVIRA_DC_nodes_STO, function(y) { if (y == 0) NA else y }), na.rm = TRUE))/DCresources[3])
U_VI_VITREEM_EAVIRA_DC_nodes_STOsd <- (100*(sd(sapply(sumVI_VITREEM_EAVIRA_DC_nodes_STO, function(y) { if (y == 0) NA else y }), na.rm = TRUE))/DCresources[3])

### NET usage 
VI_MBFD_MM_DC_nodes_NET <- matrix (VI_MBFD_MM_DC_net[,3], nc = 1000)
sumVI_MBFD_MM_DC_nodes_NET <- 0 
for (i in 1:1000) { sumVI_MBFD_MM_DC_nodes_NET[i] = sum (VI_MBFD_MM_DC_nodes_NET[,i]) }
U_VI_MBFD_MM_DC_nodes_NET <- (100*(mean(sapply(sumVI_MBFD_MM_DC_nodes_NET, function(y) { if (y == 0) NA else y }), na.rm = TRUE))/DCresources[4])
U_VI_MBFD_MM_DC_nodes_NETsd <- (100*(sd(sapply(sumVI_MBFD_MM_DC_nodes_NET, function(y) { if (y == 0) NA else y }), na.rm = TRUE))/DCresources[4])

VI_MBFD_EAVIRA_DC_nodes_NET <- matrix (VI_MBFD_EAVIRA_DC_net[,3], nc = 1000)
sumVI_MBFD_EAVIRA_DC_nodes_NET <- 0 
for (i in 1:1000) { sumVI_MBFD_EAVIRA_DC_nodes_NET[i] = sum (VI_MBFD_EAVIRA_DC_nodes_NET[,i]) }
U_VI_MBFD_EAVIRA_DC_nodes_NET <- (100*(mean(sapply(sumVI_MBFD_EAVIRA_DC_nodes_NET, function(y) { if (y == 0) NA else y }), na.rm = TRUE))/DCresources[4])
U_VI_MBFD_EAVIRA_DC_nodes_NETsd <- (100*(sd(sapply(sumVI_MBFD_EAVIRA_DC_nodes_NET, function(y) { if (y == 0) NA else y }), na.rm = TRUE))/DCresources[4])

VI_VITREEM_MM_DC_nodes_NET <- matrix (VI_VITREEM_MM_DC_net[,3], nc = 1000)
sumVI_VITREEM_MM_DC_nodes_NET <- 0 
for (i in 1:1000) { sumVI_VITREEM_MM_DC_nodes_NET[i] = sum (VI_VITREEM_MM_DC_nodes_NET[,i]) }
U_VI_VITREEM_MM_DC_nodes_NET <- (100*(mean(sapply(sumVI_VITREEM_MM_DC_nodes_NET, function(y) { if (y == 0) NA else y }), na.rm = TRUE))/DCresources[4])
U_VI_VITREEM_MM_DC_nodes_NETsd <- (100*(sd(sapply(sumVI_VITREEM_MM_DC_nodes_NET, function(y) { if (y == 0) NA else y }), na.rm = TRUE))/DCresources[4])

VI_VITREEM_EAVIRA_DC_nodes_NET <- matrix (VI_VITREEM_EAVIRA_DC_net[,3], nc = 1000)
sumVI_VITREEM_EAVIRA_DC_nodes_NET <- 0 
for (i in 1:1000) { sumVI_VITREEM_EAVIRA_DC_nodes_NET[i] = sum (VI_VITREEM_EAVIRA_DC_nodes_NET[,i]) }
U_VI_VITREEM_EAVIRA_DC_nodes_NET <- (100*(mean(sapply(sumVI_VITREEM_EAVIRA_DC_nodes_NET, function(y) { if (y == 0) NA else y }), na.rm = TRUE))/DCresources[4])
U_VI_VITREEM_EAVIRA_DC_nodes_NETsd <- (100*(sd(sapply(sumVI_VITREEM_EAVIRA_DC_nodes_NET, function(y) { if (y == 0) NA else y }), na.rm = TRUE))/DCresources[4])

U_VI <- c(U_VI_MBFD_MM_DC_nodes_NET,U_VI_MBFD_EAVIRA_DC_nodes_NET,U_VI_VITREEM_MM_DC_nodes_NET,U_VI_VITREEM_EAVIRA_DC_nodes_NET)

######

metricsCPU <- c (
	summary (sumVI_MBFD_MM_DC_nodes_CPU),
	summary(sumVI_MBFD_EAVIRA_DC_nodes_CPU),
 	summary(sumVI_VITREEM_MM_DC_nodes_CPU),
 	summary(sumVI_VITREEM_EAVIRA_DC_nodes_CPU)
 	)

metricsMEM <- c (
	summary (sumVI_MBFD_MM_DC_nodes_MEM),
	summary(sumVI_MBFD_EAVIRA_DC_nodes_MEM),
 	summary(sumVI_VITREEM_MM_DC_nodes_MEM),
 	summary(sumVI_VITREEM_EAVIRA_DC_nodes_MEM)
 	)

metricsSTO <- c (
	summary (sumVI_MBFD_MM_DC_nodes_STO),
	summary(sumVI_MBFD_EAVIRA_DC_nodes_STO),
 	summary(sumVI_VITREEM_MM_DC_nodes_STO),
 	summary(sumVI_VITREEM_EAVIRA_DC_nodes_STO)
 	)

metricsNET <- c (
	summary (sumVI_MBFD_MM_DC_nodes_NET),
	summary(sumVI_MBFD_EAVIRA_DC_nodes_NET),
 	summary(sumVI_VITREEM_MM_DC_nodes_NET),
 	summary(sumVI_VITREEM_EAVIRA_DC_nodes_NET)
 	)




par(mfrow = c(1,1))
U_cpu <- matrix ( c(
	U_VI_MBFD_EAVIRA_DC_nodes_CPU,U_VI_MBFD_MM_DC_nodes_CPU,U_VI_VITREEM_EAVIRA_DC_nodes_CPU,U_VI_VITREEM_MM_DC_nodes_CPU,
	U_VI_MBFD_EAVIRA_DC_nodes_MEM,U_VI_MBFD_MM_DC_nodes_MEM,U_VI_VITREEM_EAVIRA_DC_nodes_MEM,U_VI_VITREEM_MM_DC_nodes_MEM,
	U_VI_MBFD_EAVIRA_DC_nodes_STO,U_VI_MBFD_MM_DC_nodes_STO,U_VI_VITREEM_EAVIRA_DC_nodes_STO,U_VI_VITREEM_MM_DC_nodes_STO,
	#0,0,0,0
	U_VI_MBFD_EAVIRA_DC_nodes_NET,U_VI_MBFD_MM_DC_nodes_NET,U_VI_VITREEM_EAVIRA_DC_nodes_NET,U_VI_VITREEM_MM_DC_nodes_NET
	), nc =4 )
headerSm <- c("MBFD_MM","MBFD_EAV","VIT_MM","VIT_EAV")
colnames(U_cpu) <- unlist (headerSm)

U_cpuSD <- matrix ( c(
	U_VI_MBFD_EAVIRA_DC_nodes_CPUsd,U_VI_MBFD_MM_DC_nodes_CPUsd,U_VI_VITREEM_EAVIRA_DC_nodes_CPUsd,U_VI_VITREEM_MM_DC_nodes_CPUsd,
	U_VI_MBFD_EAVIRA_DC_nodes_MEMsd,U_VI_MBFD_MM_DC_nodes_MEMsd,U_VI_VITREEM_EAVIRA_DC_nodes_MEMsd,U_VI_VITREEM_MM_DC_nodes_MEMsd,
	U_VI_MBFD_EAVIRA_DC_nodes_STOsd,U_VI_MBFD_MM_DC_nodes_STOsd,U_VI_VITREEM_EAVIRA_DC_nodes_STOsd,U_VI_VITREEM_MM_DC_nodes_STOsd,
	#0,0,0,0
	U_VI_MBFD_EAVIRA_DC_nodes_NETsd,U_VI_MBFD_MM_DC_nodes_NETsd,U_VI_VITREEM_EAVIRA_DC_nodes_NETsd,U_VI_VITREEM_MM_DC_nodes_NETsd
	), nc =4 )
headerSm <- c("MBFD_MM","MBFD_EAVIRA","VITREEM_MM","VITREEM_EAVIRA")
colnames(U_cpuSD) <- unlist (headerSm)
upper = U_cpu+ U_cpuSD
lower = U_cpu- U_cpuSD

bp <- barplot2(U_cpu, beside = TRUE, plot.grid = TRUE, plot.ci = TRUE, ci.u = upper, ci.l = lower, 
	names.arg = c("CPU","Memory","Storage","Network"), legend = sbescLeg, #ylim = c(0,25),
    col = mycolors1, ylab = "%"#, main = c("Data center allocation resource")
    )

dev.off()