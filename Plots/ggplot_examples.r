library("ggplot2")

data <- data.frame(
    name=letters[1:5],
    value=sample(seq(4,15),5),
    sd=c(1,0.2,3,2,4)
)

ggplot(data) +
    geom_bar( aes(x=name, y=value), stat="identity", fill="skyblue", alpha=0.7) +
    geom_errorbar( aes(x=name, ymin=value-sd, ymax=value+sd), width=0.4, colour="orange", alpha=0.9, size=1.3)

ggplot(data) +
    geom_bar( aes(x=name, y=value), stat="identity", fill="skyblue", alpha=0.5) +
    geom_crossbar( aes(x=name, y=value, ymin=value-sd, ymax=value+sd), width=0.4, colour="orange", alpha=0.9, size=1.3)

ggplot(data) +
    geom_bar( aes(x=name, y=value), stat="identity", fill="skyblue", alpha=0.5) +
    geom_linerange( aes(x=name, ymin=value-sd, ymax=value+sd), colour="orange", alpha=0.9, size=1.3)

ggplot(data) +
    geom_bar( aes(x=name, y=value), stat="identity", fill="skyblue", alpha=0.5) +
    geom_pointrange( aes(x=name, y=value, ymin=value-sd, ymax=value+sd), colour="orange", alpha=0.9, size=1.3)

ggplot(data) +
    geom_errorbarh( aes(y=name, xmin=value-sd, xmax=value+sd), width=0.4, colour="orange", alpha=0.9, size=1.3)

ggplot(data) +
    geom_bar( aes(x=name, y=value), stat="identity", fill="skyblue", alpha=0.5) +
    geom_errorbar( aes(x=name, ymin=value-sd, ymax=value+sd), width=0.4, colour="orange", alpha=0.9, size=1.3) +
    coord_flip()


################# Histogram and points cloud


#Creating data 
Ixos=rnorm(4000,100,30)
Primadur=Ixos+rnorm(4000 , 0 , 30)
Ixos
Primadur
#Divide the screen in 1 line and 2 columns
par(mfrow=c(1,2),oma = c(0, 0, 2, 0))

#Make the margin around each graph a bit smaller
par(mar=c(4,2,2,2))

#Classical histogram and plot
hist(Ixos,  main="" , breaks=5 , col=rgb(0.3,0.5,1,0.4) , xlab="height" , ylab="nbr of plants")
plot(Ixos , Primadur,  main="" , pch=20 , cex=0.4 , col=rgb(0.3,0.5,1,0.4)  , xlab="primadur" , ylab="Ixos" )

#And I add only ONE title :
mtext("Primadur : Distribution and correlation with Ixos", outer = TRUE, cex = 1.5, font=4, col=rgb(0.1,0.3,0.5,0.5) )
