#install.packages(c("data.tree", "jsonlite", "curl" )) 
#install.packages(c("rjson", "RColorBrewer" )) # "reshape2", "ggplot2"))
#library(reshape2)#library(ggplot2)
library("RColorBrewer")
library("rjson")
##########################################################################################
pwd <- "~/Dropbox/UDESC/Mestrado/Pratico/CHAVE-Sim/output/"
date <- ""
#root <- "/home/daniel/output/results-31-05/"
root <- "~/results/"
#root <- paste0(toString(pwd), toString(date))
###############################___FILES___##################################################
setwd(root)
f = list.files(path=root, pattern="*.json") # , ignore.case = TRUE)
#files_max = list.files(path=root, glob2rx("*max*.json"), ignore.case = TRUE)
#files_lock = list.files(path=root, glob2rx("*lock*.json"), ignore.case = TRUE)

metrics_l = list("energy_acum_l", "energy_l")
metrics_b = list("reject_i", "accept_i", "max_host_on_i", "allocate_i", "consolidation_i", "replication_i", "overcommit_i")
azid_list = list("AZ1", "AZ2", "AZ3", "AZ4", "AZ5", "AZ6")
file_list = list(c(f[1:8]), c(f[9:16]), c(f[17:24]), c(f[25:32]), c(f[33:40]), c(f[41:48]))

file_name = list(c("m_ffff", "m_ffft", "m_fftf", "m_fftt", "m_ftff", "m_ftft", "m_fttf", "m_fttt"),
                 c("m_tfff", "m_tfft", "m_tftf", "m_tftt", "m_ttff", "m_ttft", "m_tttf", "m_tttt"),
                 c("m_rfff", "m_rfft", "m_rftf", "m_rftt", "m_rtff", "m_rtft", "m_rttf", "m_rttt"),
                 c("l_ffff", "l_ffft", "l_fftf", "l_fftt", "l_ftff", "l_ftft", "l_fttf", "l_fttt"),
                 c("l_tfff", "l_tfft", "l_tftf", "l_tftt", "l_ttff", "l_ttft", "l_tttf", "l_tttt"),
                 c("l_rfff", "l_rfft", "l_rftf", "l_rftt", "l_rtff", "l_rtft", "l_rttf", "l_rttt")
)
testFiles<-function(files){
  if(!file.exists(files)){
    print("ERROR ON: ")
    print(files)
    return(FALSE)
  }
  return(TRUE)
}

for(files in file_list){
  for(f in files){
    testFiles(f)
  }
}

plotAll000<-function(files, file_name, azid_list, metrics_b, metrics_l){
  cols<-brewer.pal(n=8,name="Set1")
  def_title <- strsplit(files[1], "lock_|max_|.json")[[1]][2]
  print(files)
  out <- tryCatch({
    filefff <- fromJSON(file = files[1])
    filefft <- fromJSON(file = files[2])
    fileftf <- fromJSON(file = files[3])
    fileftt <- fromJSON(file = files[4])
    filetff <- fromJSON(file = files[5])
    filetft <- fromJSON(file = files[6])
    filettf <- fromJSON(file = files[7])
    filettt <- fromJSON(file = files[8])
  },
  error=function(cond){
    message("ERROR:")
    message(files)
    message(cond)
    #return(NA)
  },
  warning=function(cond){
    message("WARNING:")
    message(files)
    message(cond)
    #return(NULL)
  },
  finnaly={
    message("Thats ok!")
  })
  for(az in azid_list){
    this_az <- paste0(toString(def_title ), toString("_"), toString(az))
    for(m_l in metrics_l){ 
      plotTitle <- paste0(toString(this_az), toString("_LINE_8_"), toString(m_l))
      pdfFile <- paste0(toString(plotTitle), toString('.pdf'))
      fff <- filefff[[az]][[m_l]]
      fft <- filefft[[az]][[m_l]]
      ftf <- fileftf[[az]][[m_l]]
      ftt <- fileftt[[az]][[m_l]]
      tff <- filetff[[az]][[m_l]]
      tft <- filetft[[az]][[m_l]]
      ttf <- filettf[[az]][[m_l]]
      ttt <- filettt[[az]][[m_l]]
      
      pdf(pdfFile,width=7,height=5)
      plot(fff, type="l", lwd=2, col=cols[1], lty=1, pch=1, xlab="Time Unit", ylab="Energy (W)", main=plotTitle)
      par(new = TRUE)
      plot(fft, type="l", lwd=2, col=cols[2], lty=2, pch=2, axes = FALSE, xlab="", ylab="" )
      par(new = TRUE)
      plot(ftf, type="l", lwd=2, col=cols[3], lty=3, pch=3, axes = FALSE, xlab="", ylab="" )
      par(new = TRUE)
      plot(ftt, type="l", lwd=2, col=cols[4], lty=4, pch=4, axes = FALSE, xlab="", ylab="" )
      par(new = TRUE)
      plot(tff, type="l", lwd=2, col=cols[5], lty=5, pch=5, axes = FALSE, xlab="", ylab="" )
      par(new = TRUE)
      plot(tft, type="l", lwd=2, col=cols[6], lty=6, pch=6, axes = FALSE, xlab="", ylab="" )
      par(new = TRUE)
      plot(ttf, type="l", lwd=2, col=cols[7], lty=7, pch=7, axes = FALSE, xlab="", ylab="" )
      par(new = TRUE)
      plot(ttt, type="l", lwd=2, col=cols[8], lty=8, pch=8, axes = FALSE, xlab="", ylab="" )
      par(new = TRUE)
      legend("topright", lwd=2, legend=rev(file_name), col=rev(rainbow(8)), lty=1:8, cex=0.8)
      dev.off()
    }
    
    for(m_b in metrics_b){  
      plotTitle <- paste0(toString(this_az), toString("_BAR_8_"), toString(m_b))
      pdfFile <- paste0(toString(plotTitle), toString('.pdf'))
      bfff <- filefff[[az]][[m_b]]
      bfft <- filefft[[az]][[m_b]]
      bftf <- fileftf[[az]][[m_b]]
      bftt <- fileftt[[az]][[m_b]]
      btff <- filetff[[az]][[m_b]]
      btft <- filetft[[az]][[m_b]]
      bttf <- filettf[[az]][[m_b]]
      bttt <- filettt[[az]][[m_b]]
      pdf(pdfFile,width=7,height=5)
      par(las=2)
      barplot(c(bfff, bfft, bftf, bftt, btff, btft, bttf, bttt), col=rev(rainbow(8)), xlab="Test", ylab=" unit ", main=plotTitle)
      legend("topright", lwd=2, legend=rev(file_name), col=rev(rainbow(8)), lty=1:8, cex=0.8)
      dev.off()
    }
  }
}

c <- 1
for(files in file_list){
  x0<-plotAll000(files, file_name[c], azid_list, metrics_b, metrics_l)
  c <- c+1
}

