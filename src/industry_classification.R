options(encoding = "UTF-8")
setwd("C:/Users/Leon/OneDrive/Desktop/NUS/AY22_23/Sem 1/DSA3101/Project/data")
library(readxl)
library(ggplot2)
library(tidyverse)
library(stringr)
library(tidytext)
library(textstem)


## Data Cleaning ##
ori_data = tibble(read_excel("JobsDB.xlsx"))

## Classification of Industry ##
ori_data$`Finance` = str_detect(ori_data$`Job description`, regex("financ\\w*|investm\\w*|quant\\b|trad\\w*", ignore_case=TRUE))
ori_data$`Healthcare` = str_detect(ori_data$`Job description`, regex("health\\w*|disease\\w*|hpb|medic\\w*|pharm\\w*", ignore_case=TRUE))
ori_data$`Supply, Logistics` = str_detect(ori_data$`Job description`, regex("suppl\\w*|logistic\\w*", ignore_case=TRUE))
ori_data$`Retail, Marketing` = str_detect(ori_data$`Job description`, regex("retail\\w*|sale\\w*|purchase\\w*|shop\\w*|marketi\\w+|commerc\\w*", ignore_case=TRUE))
ori_data$`Research` = str_detect(ori_data$`Job description`, regex("research\\w*", ignore_case=TRUE))
ori_data$`Public Sector` = str_detect(ori_data$`Job description`, regex("government\\w*|public sector", ignore_case=TRUE))
ori_data$`Information Technology` = str_detect(ori_data$`Job description`, regex("IT", ignore_case=FALSE)) | str_detect(ori_data$`Job description`, regex("information technology", ignore_case=TRUE))
filter(ori_data, !c(`Finance`|`Healthcare`|`Supply, Logistics`|`Retail, Marketing`|`Research`|`Public Sector`|`Information Technology`))

write.csv(ori_data, "JobsDB.xlsx")
