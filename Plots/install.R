#!/usr/bin/env Rscript
###################################################
#### This R script is part of CHAVE-SIM Project####
#### Avalable at dscar.ga/chave                ####
###################################################
############################## 0.0) LIBRARIES AND PACKAGES ####
install.packages(c("RSQLite", "ggplot2", "fmsb", "dplyr"),repos = "http://cran.us.r-project.org", quiet=TRUE)
library("dplyr", quietly=TRUE)
library("fmsb", quietly=TRUE)
library("ggplot2", quietly=TRUE)
library("DBI", quietly=TRUE)
