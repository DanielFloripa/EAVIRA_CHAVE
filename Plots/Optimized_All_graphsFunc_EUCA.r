#!/usr/bin/env Rscript
#install.packages(c("data.tree", "jsonlite", "curl" )) 
#install.packages("rjson") #  , "RColorBrewer", "rlist")) # "reshape2", "ggplot2", ))
#library(reshape2) #library(ggplot2)#library("packrat")#library("RColorBrewer")#library("rlist")
library("rjson")
##############################___FIXED TEXT_#############################################
#############################################################################################
# Migration Algorithm  || If Vm is locked, whitch state?|__| Overcomm | Consolid | Replicat |
# [l]ock, ma[x], mi[n] || [f]alse, [r]andom, [t]rue     |__| [f]alse,[t]rue                 |
##############################___FIXED TEXT_#################################################
fn <- list(
    "lf_fff", "lr_fff", "lt_fff","xf_fff", "xr_fff", "xt_fff","nf_fff", "nr_fff", "nt_fff", "EUCA",
    "lf_fft", "lr_fft", "lt_fft","xf_fft", "xr_fft", "xt_fft","nf_fft", "nr_fft", "nt_fft", "EUCA",
    "lf_ftf", "lr_ftf", "lt_ftf","xf_ftf", "xr_ftf", "xt_ftf","nf_ftf", "nr_ftf", "nt_ftf", "EUCA",
    "lf_ftt", "lr_ftt", "lt_ftt","xf_ftt", "xr_ftt", "xt_ftt","nf_ftt", "nr_ftt", "nt_ftt", "EUCA",
    "lf_tff", "lr_tff", "lt_tff","xf_tff", "xr_tff", "xt_tff","nf_tff", "nr_tff", "nt_tff", "EUCA",
    "lf_tft", "lr_tft", "lt_tft","xf_tft", "xr_tft", "xt_tft","nf_tft", "nr_tft", "nt_tft", "EUCA",
    "lf_ttf", "lr_ttf", "lt_ttf","xf_ttf", "xr_ttf", "xt_ttf","nf_ttf", "nr_ttf", "nt_ttf", "EUCA",
    "lf_ttt", "lr_ttt", "lt_ttt","xf_ttt", "xr_ttt", "xt_ttt","nf_ttt", "nr_ttt", "nt_ttt", "EUCA")

subtl = "Legend (AlgCons,Lock)_(Ovc,Cons,Repl)"

##############################___MAIN PARAMETERS AND DIRS_#################################
# Get the parameter:
date = commandArgs(trailingOnly=TRUE)
fileEUCA = "/home/debian/Dropbox/UDESC/Mestrado/Pratico/CHAVE-Sim/output/18.06.05-12.36.15/results/18.06.05-12.36.15_EUCA_FFD2I_1_LOCK_LRANDOM_OTrue_CTrue_RTrue.json"
pwd <- "~/Dropbox/UDESC/Mestrado/Pratico/CHAVE-Sim/output/"
root <- paste0(toString(pwd), toString(date[1]), toString("/results"))

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
    message(root)
})

##############################___FILES___##################################################
f <- list.files(path=root, pattern="*.json") # , ignore.case = TRUE)
metrics_l <- list("energy_acum_l", "energy_l")
metrics_b <- list("reject_i", "max_host_on_i", "consolidation_i", "replication_i", "overcommit_i") # , "accept_i", "allocate_i"
azid_list <- list("AZ1", "AZ2", "AZ3", "AZ4", "AZ5", "AZ6")  # , 'global'

comment<-function(){
    S <- length(f)
    S_leg <- length(fn)
    
    file_list <- list(seq(1,S))
    leg <- list(seq(1,S_leg))
    
    group_size <- 8
    n <- 0
    
    len <-S/group_size
    len_leg <-S_leg/group_size
    
    for (i in 1:len){
        xx<-1+(n*group_size)
        yy<-i*group_size
        file_list[[i]] <- c(f[xx: yy])
        n <- n + 1
    }
    
    leg[[1]] <- c(subtl)
    n <- 0
    for (i in 2:len_leg+1){
        xx<-1+(n*group_size)
        yy<-i*group_size
        leg[[i]] <- c(fn[xx: yy])
        n <- n + 1
    }
}

S <- length(fn)
ordered_f <- list(seq(1,S))
group_size <- 9
n <- 0
len <-S/group_size

file_list <- list(seq(1,len))
leg <- list(seq(1,len))

for (i in 1:len){
    xx<-1+(n*group_size)
    yy<-i*group_size
    file_list[[i]] <- c(f[xx: yy])
    leg[[i]] <- c(fn[xx: yy])
    n <- n + 1
}

#print(S)
#print(length(f))
#print(length(leg))
#print(length(file_list))
#print(leg)

testFiles<-function(files){
    if(!file.exists(files)){
        print("ERROR ON: ")
        print(files)
        return(FALSE)
    }
    return(TRUE)
}
for(files in file_list){
    for(ff in files){
        testFiles(ff)
    }
}
##############################___FUNCTIONS___#############################################

my_colors <- rainbow(9)
plotAll000<-function(files, legen, azid_list, metrics_b, metrics_l){
    file_name <- strsplit(files[1], ".json")[[1]]
    title_list = strsplit(file_name, "_")[[1]]
    date <- title_list[1]
    algo <- title_list[2]
    orde <- title_list[3]
    wt <- title_list[4]
    algCons <- title_list[5]
    locked <- title_list[6]  
    #overcom <- title_list[7]  #cons <- title_list[8]  #repl <- title_list[9]
    title_0 <- paste0(toString(date), toString(" "), toString(algo))
    pdf_file <- paste0(toString(date), toString("_"), toString(algo), toString("_"), 
                       toString(orde), toString("_"), toString(wt), toString("_"), 
                       toString(algCons), toString("_"), toString(locked), toString("_O_C_R"))
    out <- tryCatch({
        filefff <- fromJSON(file = files[1])
        filefft <- fromJSON(file = files[2])
        fileftf <- fromJSON(file = files[3])
        fileftt <- fromJSON(file = files[4])
        filetff <- fromJSON(file = files[5])
        filetft <- fromJSON(file = files[6])
        filettf <- fromJSON(file = files[7])
        filettt <- fromJSON(file = files[8])
        f_EUCA <- fromJSON(file = fileEUCA)
    },
    error=function(cond){
        message("ERROR:")
        message(files)
        message(cond)
    },
    warning=function(cond){
        message("WARNING:")
        message(files)
        message(cond)
    },
    finnaly={
        message(paste0(toString("Running: "), toString(file_name)))
    })
    for(az in azid_list){
        pdf_file0 <- paste0(toString(pdf_file), toString("_"), toString(az))
        title_1 <- paste0(toString(title_0), toString(" "), toString(az))
        for(m_l in metrics_l){
            fileEUCA 
            title_2line <- paste0(toString(title_1), toString(" "), toString(m_l))
            pdfFile <- paste0(toString(pdf_file0), toString("_LINE8_"), toString(m_l), toString('.pdf'))
            EUCA <- f_EUCA[[az]][[m_l]]
            print(EUCA)
            fff <- filefff[[az]][[m_l]]
            fft <- filefft[[az]][[m_l]]
            ftf <- fileftf[[az]][[m_l]]
            ftt <- fileftt[[az]][[m_l]]
            tff <- filetff[[az]][[m_l]]
            tft <- filetft[[az]][[m_l]]
            ttf <- filettf[[az]][[m_l]]
            ttt <- filettt[[az]][[m_l]]
            pdf(pdfFile,width=7,height=5)
            plot(fff, type="l", lwd=1, col=my_colors[1], lty=1, pch=1, xlab="Time Unit", ylab="Energy (W)", main=title_2line, cex.main=0.9, sub=subtl)
            par(new = TRUE)
            plot(fft, type="l", lwd=1, col=my_colors[2], lty=2, pch=2, axes = FALSE, xlab="", ylab="" )
            par(new = TRUE)
            plot(ftf, type="l", lwd=1, col=my_colors[3], lty=3, pch=3, axes = FALSE, xlab="", ylab="" )
            par(new = TRUE)
            plot(ftt, type="l", lwd=1, col=my_colors[4], lty=4, pch=4, axes = FALSE, xlab="", ylab="" )
            par(new = TRUE)
            plot(tff, type="l", lwd=1, col=my_colors[5], lty=5, pch=5, axes = FALSE, xlab="", ylab="" )
            par(new = TRUE)
            plot(tft, type="l", lwd=1, col=my_colors[6], lty=6, pch=6, axes = FALSE, xlab="", ylab="" )
            par(new = TRUE)
            plot(ttf, type="l", lwd=1, col=my_colors[7], lty=7, pch=7, axes = FALSE, xlab="", ylab="" )
            par(new = TRUE)
            plot(ttt, type="l", lwd=1, col=my_colors[8], lty=8, pch=8, axes = FALSE, xlab="", ylab="" )
            par(new = TRUE)
            #plot(EUCA, type="l", lwd=1, col=my_colors[9], lty=9, pch=9, axes = FALSE, xlab="", ylab="" )
            #par(new = TRUE)
            ##c("bottomright", "bottom", "bottomleft", "left", "topleft", "top", "topright", "right", "center"))
            legend("topleft", lwd=2, legend=legen, col=rainbow(9), lty=1:9, cex=0.9)
            dev.off()
        }
        for(m_b in metrics_b){
            title_2bar <- paste0(toString(title_1), toString(" "), toString(m_b))
            pdfFile_b <- paste0(toString(pdf_file0), toString("_BAR8_"), toString(m_b), toString('.pdf'))
            bfff <- filefff[[az]][[m_b]]
            bfft <- filefft[[az]][[m_b]]
            bftf <- fileftf[[az]][[m_b]]
            bftt <- fileftt[[az]][[m_b]]
            btff <- filetff[[az]][[m_b]]
            btft <- filetft[[az]][[m_b]]
            bttf <- filettf[[az]][[m_b]]
            bttt <- filettt[[az]][[m_b]]
            pdf(pdfFile_b,width=7,height=5)
            par(las=1)
            par(mar=c(5,8,4,2))
            dat<-c(bfff, bfft,bftf,bftt,btff,btft,bttf,bttt)
            barplot(dat, col=my_colors, xlab=subtl, ylab="Metric Units", main=title_2bar, cex.main=0.9, names.arg=legen, beside = TRUE)
            ##legend(x="topright", lwd=2, legend=legen, col=rainbow(8), cex=0.7) # , pch=15, bty="n"
            dev.off()
        }
    }
}

g <- 1
#print(file_list)
for(files in file_list){
    x0<-plotAll000(files, leg[[g]], azid_list, metrics_b, metrics_l)
    g <- g+1
}

warnings()

