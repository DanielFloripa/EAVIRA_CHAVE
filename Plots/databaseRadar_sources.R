# sources table for databaseRadar.R
#Sys.setenv("plotly_username"="Daniel13")
#Sys.setenv("plotly_api_key"="tEEharsCr0RaDBhGsmqB")
#streamming<-"1mvsw4web5"

#devtools::install_github("ropensci/plotly")
#library(plotly)

#options(browser = 'false')
#api_create(p, filename = "r-docs-midwest-boxplots")

metric2<-"t.gvt as gvt, t.energy_0, t.energy_f, max(t.energy_0-t.energy_f) as reduc_val, (t.energy_0-t.energy_f)/t.energy_0 as reduc_p, t.val_0 as fals_pos, t.val_f as migrations, l.val_0 as load, t.info as info"


AZ_ERR_CONS<-data.frame(
  AZ1<-matrix(c(
    "Cons_AA0", 39, 0.01, "SELECT t.t.gvt as gvt, t.energy_0, t.energy_f, max(t.energy_0-t.energy_f) as reduc_val, (t.energy_0-t.energy_f)/t.energy_0 as reduc_p, t.val_0 as fals_pos, t.val_f as migrations, l.val_0 as load, t.info as info, l.val_0 as load FROM consol_d as t inner join az_load_l as l on l.gvt=t.gvt and (l.val_0 <= 0.26320513 and l.val_0 >= 0.24320513)",
    "CHAVE_AA0", 23, 0.05, "SELECT t.t.gvt as gvt, t.energy_0, t.energy_f, max(t.energy_0-t.energy_f) as reduc_val, (t.energy_0-t.energy_f)/t.energy_0 as reduc_p, t.val_0 as fals_pos, t.val_f as migrations, l.val_0 as load, t.info as info, l.val_0 as load FROM consol_d as t inner join az_load_l as l on l.gvt=t.gvt and (l.val_0 <= 0.30320513 and l.val_0 >= 0.20320513)",
    "Cons_AA20", 24, 0.01, "SELECT t.t.gvt as gvt, t.energy_0, t.energy_f, max(t.energy_0-t.energy_f) as reduc_val, (t.energy_0-t.energy_f)/t.energy_0 as reduc_p, t.val_0 as fals_pos, t.val_f as migrations, l.val_0 as load, t.info as info, l.val_0 as load FROM consol_d as t inner join az_load_l as l on l.gvt=t.gvt and (l.val_0 <= 0.26320513 and l.val_0 >= 0.24320513)",
    "CHAVE_AA20", 17, 0.01, "SELECT t.t.gvt as gvt, t.energy_0, t.energy_f, max(t.energy_0-t.energy_f) as reduc_val, (t.energy_0-t.energy_f)/t.energy_0 as reduc_p, t.val_0 as fals_pos, t.val_f as migrations, l.val_0 as load, t.info as info, l.val_0 as load FROM consol_d as t inner join az_load_l as l on l.gvt=t.gvt and (l.val_0 <= 0.26320513 and l.val_0 >= 0.24320513)",
    "Cons_MAX", 18, 0.01, "SELECT t.t.gvt as gvt, t.energy_0, t.energy_f, max(t.energy_0-t.energy_f) as reduc_val, (t.energy_0-t.energy_f)/t.energy_0 as reduc_p, t.val_0 as fals_pos, t.val_f as migrations, l.val_0 as load, t.info as info, l.val_0 as load FROM consol_d as t inner join az_load_l as l on l.gvt=t.gvt and (l.val_0 <= 0.26320513 and l.val_0 >= 0.24320513)",
    "CHAVE_MAX", 7, 0.01, "SELECT t.t.gvt as gvt, t.energy_0, t.energy_f, max(t.energy_0-t.energy_f) as reduc_val, (t.energy_0-t.energy_f)/t.energy_0 as reduc_p, t.val_0 as fals_pos, t.val_f as migrations, l.val_0 as load, t.info as info, l.val_0 as load FROM consol_d as t inner join az_load_l as l on l.gvt=t.gvt and (l.val_0 <= 0.26320513 and l.val_0 >= 0.24320513)"), ncol=4, byrow = TRUE),
  AZ5<-matrix(c(
    "Cons_AA0", 75, 0.01, "SELECT t.t.gvt as gvt, t.energy_0, t.energy_f, max(t.energy_0-t.energy_f) as reduc_val, (t.energy_0-t.energy_f)/t.energy_0 as reduc_p, t.val_0 as fals_pos, t.val_f as migrations, l.val_0 as load, t.info as info, l.val_0 as load FROM consol_d as t inner join az_load_l as l on l.gvt=t.gvt and (l.val_0 <= 0.72471774 and l.val_0 >= 0.70471774)",
    "CHAVE_AA0", 24, 0.03, "SELECT t.t.gvt as gvt, t.energy_0, t.energy_f, max(t.energy_0-t.energy_f) as reduc_val, (t.energy_0-t.energy_f)/t.energy_0 as reduc_p, t.val_0 as fals_pos, t.val_f as migrations, l.val_0 as load, t.info as info, l.val_0 as load FROM consol_d as t inner join az_load_l as l on l.gvt=t.gvt and (l.val_0 <= 0.74471774 and l.val_0 >= 0.68471774)",
    "Cons_AA20", 129, 0.01, "SELECT t.t.gvt as gvt, t.energy_0, t.energy_f, max(t.energy_0-t.energy_f) as reduc_val, (t.energy_0-t.energy_f)/t.energy_0 as reduc_p, t.val_0 as fals_pos, t.val_f as migrations, l.val_0 as load, t.info as info, l.val_0 as load FROM consol_d as t inner join az_load_l as l on l.gvt=t.gvt and (l.val_0 <= 0.72471774 and l.val_0 >= 0.70471774)",
    "CHAVE_AA20", 48, 0.02, "SELECT t.t.gvt as gvt, t.energy_0, t.energy_f, max(t.energy_0-t.energy_f) as reduc_val, (t.energy_0-t.energy_f)/t.energy_0 as reduc_p, t.val_0 as fals_pos, t.val_f as migrations, l.val_0 as load, t.info as info, l.val_0 as load FROM consol_d as t inner join az_load_l as l on l.gvt=t.gvt and (l.val_0 <= 0.73471774 and l.val_0 >= 0.69471774)",
    "Cons_MAX", 7, 0.01, "SELECT t.t.gvt as gvt, t.energy_0, t.energy_f, max(t.energy_0-t.energy_f) as reduc_val, (t.energy_0-t.energy_f)/t.energy_0 as reduc_p, t.val_0 as fals_pos, t.val_f as migrations, l.val_0 as load, t.info as info, l.val_0 as load FROM consol_d as t inner join az_load_l as l on l.gvt=t.gvt and (l.val_0 <= 0.72471774 and l.val_0 >= 0.70471774)",
    "CHAVE_MAX", 8, 0.01, "SELECT t.t.gvt as gvt, t.energy_0, t.energy_f, max(t.energy_0-t.energy_f) as reduc_val, (t.energy_0-t.energy_f)/t.energy_0 as reduc_p, t.val_0 as fals_pos, t.val_f as migrations, l.val_0 as load, t.info as info, l.val_0 as load FROM consol_d as t inner join az_load_l as l on l.gvt=t.gvt and (l.val_0 <= 0.72471774 and l.val_0 >= 0.70471774)"), ncol=4, byrow = TRUE),
  AZ6<-matrix(c(
    "Cons_AA0", 594, 0.01, "SELECT t.t.gvt as gvt, t.energy_0, t.energy_f, max(t.energy_0-t.energy_f) as reduc_val, (t.energy_0-t.energy_f)/t.energy_0 as reduc_p, t.val_0 as fals_pos, t.val_f as migrations, l.val_0 as load, t.info as info, l.val_0 as load FROM consol_d as t inner join az_load_l as l on l.gvt=t.gvt and (l.val_0 <= 0.65648438 and l.val_0 >= 0.63648438)",
    "CHAVE_AA0", 30, 0.01, "SELECT t.t.gvt as gvt, t.energy_0, t.energy_f, max(t.energy_0-t.energy_f) as reduc_val, (t.energy_0-t.energy_f)/t.energy_0 as reduc_p, t.val_0 as fals_pos, t.val_f as migrations, l.val_0 as load, t.info as info, l.val_0 as load FROM consol_d as t inner join az_load_l as l on l.gvt=t.gvt and (l.val_0 <= 0.65648438 and l.val_0 >= 0.63648438)",
    "Cons_AA20", 1640, 0.01, "SELECT t.t.gvt as gvt, t.energy_0, t.energy_f, max(t.energy_0-t.energy_f) as reduc_val, (t.energy_0-t.energy_f)/t.energy_0 as reduc_p, t.val_0 as fals_pos, t.val_f as migrations, l.val_0 as load, t.info as info, l.val_0 as load FROM consol_d as t inner join az_load_l as l on l.gvt=t.gvt and (l.val_0 <= 0.65648438 and l.val_0 >= 0.63648438)",
    "CHAVE_AA20", 95, 0.01, "SELECT t.t.gvt as gvt, t.energy_0, t.energy_f, max(t.energy_0-t.energy_f) as reduc_val, (t.energy_0-t.energy_f)/t.energy_0 as reduc_p, t.val_0 as fals_pos, t.val_f as migrations, l.val_0 as load, t.info as info, l.val_0 as load FROM consol_d as t inner join az_load_l as l on l.gvt=t.gvt and (l.val_0 <= 0.65648438 and l.val_0 >= 0.63648438)",
    "Cons_MAX", 26, 0.01, "SELECT t.t.gvt as gvt, t.energy_0, t.energy_f, max(t.energy_0-t.energy_f) as reduc_val, (t.energy_0-t.energy_f)/t.energy_0 as reduc_p, t.val_0 as fals_pos, t.val_f as migrations, l.val_0 as load, t.info as info, l.val_0 as load FROM consol_d as t inner join az_load_l as l on l.gvt=t.gvt and (l.val_0 <= 0.65648438 and l.val_0 >= 0.63648438)",
    "CHAVE_MAX", 6, 0.01, "SELECT t.t.gvt as gvt, t.energy_0, t.energy_f, max(t.energy_0-t.energy_f) as reduc_val, (t.energy_0-t.energy_f)/t.energy_0 as reduc_p, t.val_0 as fals_pos, t.val_f as migrations, l.val_0 as load, t.info as info, l.val_0 as load FROM consol_d as t inner join az_load_l as l on l.gvt=t.gvt and (l.val_0 <= 0.65648438 and l.val_0 >= 0.63648438)"), ncol=4, byrow = TRUE))

