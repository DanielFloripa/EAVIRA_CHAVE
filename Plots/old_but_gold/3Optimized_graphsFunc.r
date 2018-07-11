#install.packages(c("data.tree", "jsonlite", "curl" )) 
#install.packages(c("rjson", "RColorBrewer" )) # "reshape2", "ggplot2"))
#library(reshape2)#library(ggplot2)
library("RColorBrewer")
library("rjson")
##########################################################################################
#root <- "~/Dropbox/UDESC/Mestrado/Pratico/CHAVE-Sim/output/results/"
#root <- "/home/daniel/output/results-31-05/"
root <- "~/results/"
date <- "18.05.31_"
base <- paste0(toString(root), toString(date))
###############################___MAX___##################################################
# Lock False
f_cm_ffff <- paste0(toString(base), toString('03.57.59_CHAVE_max_FFD2I_1_LFalse_OFalse_CFalse_RFalse.json'))
f_cm_ffft <- paste0(toString(base), toString('03.57.45_CHAVE_max_FFD2I_1_LFalse_OFalse_CFalse_RTrue.json'))
f_cm_fftf <- paste0(toString(base), toString('03.57.15_CHAVE_max_FFD2I_1_LFalse_OFalse_CTrue_RFalse.json'))
f_cm_fftt <- paste0(toString(base), toString('03.56.52_CHAVE_max_FFD2I_1_LFalse_OFalse_CTrue_RTrue.json'))
f_cm_ftff <- paste0(toString(base), toString('03.55.34_CHAVE_max_FFD2I_1_LFalse_OTrue_CFalse_RFalse.json'))
f_cm_ftft <- paste0(toString(base), toString('03.55.06_CHAVE_max_FFD2I_1_LFalse_OTrue_CFalse_RTrue.json'))
f_cm_fttf <- paste0(toString(base), toString('03.54.53_CHAVE_max_FFD2I_1_LFalse_OTrue_CTrue_RFalse.json'))
f_cm_fttt <- paste0(toString(base), toString('03.54.34_CHAVE_max_FFD2I_1_LFalse_OTrue_CTrue_RTrue.json'))
# Lock True
f_cm_tfff <- paste0(toString(base), toString('04.02.02_CHAVE_max_FFD2I_1_LTrue_OFalse_CFalse_RFalse.json'))
f_cm_tfft <- paste0(toString(base), toString('04.01.26_CHAVE_max_FFD2I_1_LTrue_OFalse_CFalse_RTrue.json'))
f_cm_tftf <- paste0(toString(base), toString('04.00.43_CHAVE_max_FFD2I_1_LTrue_OFalse_CTrue_RFalse.json'))
f_cm_tftt <- paste0(toString(base), toString('03.59.37_CHAVE_max_FFD2I_1_LTrue_OFalse_CTrue_RTrue.json'))
f_cm_ttff <- paste0(toString(base), toString('03.59.27_CHAVE_max_FFD2I_1_LTrue_OTrue_CFalse_RFalse.json'))
f_cm_ttft <- paste0(toString(base), toString('03.59.26_CHAVE_max_FFD2I_1_LTrue_OTrue_CFalse_RTrue.json'))
f_cm_tttf <- paste0(toString(base), toString('03.59.17_CHAVE_max_FFD2I_1_LTrue_OTrue_CTrue_RFalse.json'))
f_cm_tttt <- paste0(toString(base), toString('03.58.49_CHAVE_max_FFD2I_1_LTrue_OTrue_CTrue_RTrue.json'))
# Lock Random
f_cm_rfff <- paste0(toString(base), toString('03.52.57_CHAVE_max_FFD2I_1_LRandom_OFalse_CFalse_RFalse.json'))
f_cm_rfft <- paste0(toString(base), toString('03.52.26_CHAVE_max_FFD2I_1_LRandom_OFalse_CFalse_RTrue.json'))
f_cm_rftf <- paste0(toString(base), toString('03.52.19_CHAVE_max_FFD2I_1_LRandom_OFalse_CTrue_RFalse.json'))
f_cm_rftt <- paste0(toString(base), toString('03.52.19_CHAVE_max_FFD2I_1_LRandom_OFalse_CTrue_RTrue.json'))
f_cm_rtff <- paste0(toString(base), toString('03.51.34_CHAVE_max_FFD2I_1_LRandom_OTrue_CFalse_RFalse.json'))
f_cm_rtft <- paste0(toString(base), toString('03.51.22_CHAVE_max_FFD2I_1_LRandom_OTrue_CFalse_RTrue.json'))
f_cm_rttf <- paste0(toString(base), toString('03.51.13_CHAVE_max_FFD2I_1_LRandom_OTrue_CTrue_RFalse.json'))
f_cm_rttt <- paste0(toString(base), toString('03.50.52_CHAVE_max_FFD2I_1_LRandom_OTrue_CTrue_RTrue.json'))
###############################___LOCK___#################################################
f_cl_ffff <- paste0(toString(base), toString('03.41.47_CHAVE_lock_FFD2I_1_LFalse_OFalse_CFalse_RFalse.json'))
f_cl_ffft <- paste0(toString(base), toString('03.41.47_CHAVE_lock_FFD2I_1_LFalse_OFalse_CFalse_RTrue.json'))
f_cl_fftf <- paste0(toString(base), toString('03.41.47_CHAVE_lock_FFD2I_1_LFalse_OFalse_CTrue_RFalse.json'))
f_cl_fftt <- paste0(toString(base), toString('03.41.47_CHAVE_lock_FFD2I_1_LFalse_OFalse_CTrue_RTrue.json'))
f_cl_ftff <- paste0(toString(base), toString('03.41.47_CHAVE_lock_FFD2I_1_LFalse_OTrue_CFalse_RFalse.json'))
f_cl_ftft <- paste0(toString(base), toString('03.41.47_CHAVE_lock_FFD2I_1_LFalse_OTrue_CFalse_RTrue.json'))
f_cl_fttf <- paste0(toString(base), toString('03.41.47_CHAVE_lock_FFD2I_1_LFalse_OTrue_CTrue_RFalse.json'))
f_cl_fttt <- paste0(toString(base), toString('03.41.47_CHAVE_lock_FFD2I_1_LFalse_OTrue_CTrue_RTrue.json'))
#
f_cl_tfff <- paste0(toString(base), toString('03.49.05_CHAVE_lock_FFD2I_1_LTrue_OFalse_CFalse_RFalse.json'))
f_cl_tfft <- paste0(toString(base), toString('03.49.00_CHAVE_lock_FFD2I_1_LTrue_OFalse_CFalse_RTrue.json'))
f_cl_tftf <- paste0(toString(base), toString('03.49.00_CHAVE_lock_FFD2I_1_LTrue_OFalse_CTrue_RFalse.json'))
f_cl_tftt <- paste0(toString(base), toString('03.48.58_CHAVE_lock_FFD2I_1_LTrue_OFalse_CTrue_RTrue.json'))
f_cl_ttff <- paste0(toString(base), toString('03.48.37_CHAVE_lock_FFD2I_1_LTrue_OTrue_CFalse_RFalse.json'))
f_cl_ttft <- paste0(toString(base), toString('03.48.37_CHAVE_lock_FFD2I_1_LTrue_OTrue_CFalse_RTrue.json'))
f_cl_tttf <- paste0(toString(base), toString('03.48.37_CHAVE_lock_FFD2I_1_LTrue_OTrue_CTrue_RFalse.json'))
f_cl_tttt <- paste0(toString(base), toString('03.48.07_CHAVE_lock_FFD2I_1_LTrue_OTrue_CTrue_RTrue.json'))
#
f_cl_rfff <- paste0(toString(base), toString('03.41.47_CHAVE_lock_FFD2I_1_LRandom_OFalse_CFalse_RFalse.json'))
f_cl_rfft <- paste0(toString(base), toString('03.41.47_CHAVE_lock_FFD2I_1_LRandom_OFalse_CFalse_RTrue.json'))
f_cl_rftf <- paste0(toString(base), toString('03.41.47_CHAVE_lock_FFD2I_1_LRandom_OFalse_CTrue_RFalse.json'))
f_cl_rftt <- paste0(toString(base), toString('03.41.47_CHAVE_lock_FFD2I_1_LRandom_OFalse_CTrue_RTrue.json'))
f_cl_rtff <- paste0(toString(base), toString('03.41.47_CHAVE_lock_FFD2I_1_LRandom_OTrue_CFalse_RFalse.json'))
f_cl_rtft <- paste0(toString(base), toString('03.41.47_CHAVE_lock_FFD2I_1_LRandom_OTrue_CFalse_RTrue.json'))
f_cl_rttf <- paste0(toString(base), toString('03.41.47_CHAVE_lock_FFD2I_1_LRandom_OTrue_CTrue_RFalse.json'))
f_cl_rttt <- paste0(toString(base), toString('03.41.47_CHAVE_lock_FFD2I_1_LRandom_OTrue_CTrue_RTrue.json'))
###############################___EUCA___#################################################
#f_ff_em <- paste0(toString(date), toString('EUCA_max_FFD2I_1_20_False_False.json'))
#f_tf_em <- paste0(toString(root), toString('EUCA_max_FFD2I_1_20_True_False.json'))
##########################################################################################

metrics_l = list('energy_acum_l', "energy_l")
metrics_b = list('reject_i', 'accept_i')  #, 'max_host_on_i', 'allocate_i', 'consolidation_i', 'replication_i', 'overcommit_i', )
azid_list = list('AZ1', 'AZ2', 'AZ3', 'AZ4', 'AZ5', 'AZ6')
file_list = list(c(f_cm_ffff, f_cm_ffft, f_cm_fftf, f_cm_fftt),
                 c(f_cm_ftff, f_cm_ftft, f_cm_fttf, f_cm_fttt),
                 c(f_cm_tfff, f_cm_tfft, f_cm_tftf, f_cm_tftt),
                 c(f_cm_ttff, f_cm_ttft, f_cm_tttf, f_cm_tttt),
                 c(f_cm_rfff, f_cm_rfft, f_cm_rftf, f_cm_rftt),
                 c(f_cm_rtff, f_cm_rtft, f_cm_rttf, f_cm_rttt),
                 c(f_cl_ffff, f_cl_ffft, f_cl_fftf, f_cl_fftt),
                 c(f_cl_ftff, f_cl_ftft, f_cl_fttf, f_cl_fttt),
                 c(f_cl_tfff, f_cl_tfft, f_cl_tftf, f_cl_tftt),
                 c(f_cl_ttff, f_cl_ttft, f_cl_tttf, f_cl_tttt),
                 c(f_cl_rfff, f_cl_rfft, f_cl_rftf, f_cl_rftt),
                 c(f_cl_rtff, f_cl_rtft, f_cl_rttf, f_cl_rttt)
)

file_name = list(list('f_cm_ffff', 'f_cm_ffft', 'f_cm_fftf', 'f_cm_fftt'),
                 list('f_cm_ftff', 'f_cm_ftft', 'f_cm_fttf', 'f_cm_fttt'),
                 list('f_cm_tfff', 'f_cm_tfft', 'f_cm_tftf', 'f_cm_tftt'),
                 list('f_cm_ttff', 'f_cm_ttft', 'f_cm_tttf', 'f_cm_tttt'),
                 list('f_cm_rfff', 'f_cm_rfft', 'f_cm_rftf', 'f_cm_rftt'),
                 list('f_cm_rtff', 'f_cm_rtft', 'f_cm_rttf', 'f_cm_rttt'),
                 list('f_cl_ffff', 'f_cl_ffft', 'f_cl_fftf', 'f_cl_fftt'),
                 list('f_cl_ftff', 'f_cl_ftft', 'f_cl_fttf', 'f_cl_fttt'),
                 list('f_cl_tfff', 'f_cl_tfft', 'f_cl_tftf', 'f_cl_tftt'),
                 list('f_cl_ttff', 'f_cl_ttft', 'f_cl_tttf', 'f_cl_tttt'),
                 list('f_cl_rfff', 'f_cl_rfft', 'f_cl_rftf', 'f_cl_rftt'),
                 list('f_cl_rtff', 'f_cl_rtft', 'f_cl_rttf', 'f_cl_rttt')
)

testFiles<-function(files){
  if(!file.exists(files)){
    print("ERROR ON: ")
    print(files)
    return(FALSE)
  }
  return(TRUE)
}

plotAll000<-function(files, file_name, azid_list, metrics_b, metrics_l){
  cols<-brewer.pal(n=4,name="Set1")
  fileff <- fromJSON(file = files[1])
  filett <- fromJSON(file = files[2])
  fileft <- fromJSON(file = files[3])
  filetf <- fromJSON(file = files[4])
  
  for(az in azid_list){
    for(m_l in metrics_l){ 
      plotTitle <- paste0(toString(az), toString("_LINE_4_"), toString(m_l))
      pdfFile <- paste0(toString(files[1]), toString(plotTitle), toString('.pdf'))
      az_ffl <- fileff[[az]][[m_l]]
      az_ttl <- filett[[az]][[m_l]]
      az_ftl <- fileft[[az]][[m_l]]
      az_tfl <- filetf[[az]][[m_l]]
      
      pdf(pdfFile,width=7,height=5)
      plot(az_ffl, type="l", lwd=3, col=cols[1], lty=1, pch=1, xlab="Time Unit", ylab="Energy (W)", main=plotTitle)
      par(new = TRUE)
      plot(az_ttl, type="l", lwd=3, col=cols[2], lty=2, pch=2, axes = FALSE, xlab="", ylab="" )
      par(new = TRUE)
      plot(az_tfl, type="l", lwd=3, col=cols[3], lty=3, pch=3, axes = FALSE, xlab="", ylab="" )
      par(new = TRUE)
      plot(az_ftl, type="l", lwd=3, col=cols[4], lty=4, pch=4, axes = FALSE, xlab="", ylab="" )
      legend("topright", lwd=3, legend=file_name, col=cols, lty=1:4, cex=0.8)
      dev.off()
    }
    
    for(m_b in metrics_b){  
      plotTitle <- paste0(toString(az), toString("_BAR_4_"), toString(m_b))
      pdfFile <- paste0(toString(files[1]), toString(plotTitle), toString('.pdf'))
      az_ffb <- fileff[[az]][[m_b]]
      az_ttb <- filett[[az]][[m_b]]
      az_ftb <- fileft[[az]][[m_b]]
      az_tfb <- filetf[[az]][[m_b]]  
      pdf(pdfFile,width=7,height=5)
      barplot(c(az_ffb, az_ttb, az_tfb, az_ftb), col=cols, xlab="Test", ylab="Energy (W)", main=plotTitle)
      legend("topright", lwd=3, legend=file_name, col=cols, lty=1:4, cex=0.8)
      dev.off()
    }
  }
}

for(files in file_list){
  for(f in files){
    testFiles(f)
  }
}

c <- 1
for(files in file_list){
  x0<-plotAll000(files, file_name[c], azid_list, metrics_b, metrics_l)
  c <- c+1
}

OLD_file_list=list(c(f_cm_ffff, f_cm_ffft, f_cm_fftf, f_cm_fftt,
                 f_cm_ftff, f_cm_ftft, f_cm_fttf, f_cm_fttt,
                 f_cm_tfff, f_cm_tfft, f_cm_tftf, f_cm_tftt,
                 f_cm_ttff, f_cm_ttft, f_cm_tttf, f_cm_tttt,
                 f_cm_rfff, f_cm_rfft, f_cm_rftf, f_cm_rftt,
                 f_cm_rtff, f_cm_rtft, f_cm_rttf, f_cm_rttt),
               c(f_cl_ffff, f_cl_ffft, f_cl_fftf, f_cl_fftt,
                 f_cl_ftff, f_cl_ftft, f_cl_fttf, f_cl_fttt,
                 f_cl_tfff, f_cl_tfft, f_cl_tftf, f_cl_tftt,
                 f_cl_ttff, f_cl_ttft, f_cl_tttf, f_cl_tttt,
                 f_cl_rfff, f_cl_rfft, f_cl_rftf, f_cl_rftt,
                 f_cl_rtff, f_cl_rtft, f_cl_rttf, f_cl_rttt)
)
