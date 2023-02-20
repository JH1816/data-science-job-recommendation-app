FROM rocker/shiny-verse
RUN sudo apt update && sudo apt install -y libxt-dev
RUN sudo apt -y upgrade
RUN sudo apt install -y libxml2 libxml2-dev libudunits2-dev
RUN install2.r tidyverse httr jsonlite plotly flexdashboard DT shinydashboard shinyjs leaflet
COPY app.R /srv/shiny-server/app.R
COPY final_df.Rda /srv/shiny-server/final_df.Rda
COPY companyLocation.Rda /srv/shiny-server/companyLocation.Rda

