#
# This is a Shiny web application. You can run the application by clicking
# the 'Run App' button above.
#
# Find out more about building applications with Shiny here:
#
#    http://shiny.rstudio.com/
#

library(shiny)
library(shinydashboard)
library(shinyjs)
library(tidyverse)
library(plotly)
library(httr)
library(jsonlite)
library(DT)
library(leaflet)


jscode <- "
shinyjs.collapse = function(boxid) {
$('#' + boxid).closest('.box').find('[data-widget=collapse]').click();
}
"


nullToNA <- function(x) {
    x[sapply(x, is.null)] <- NA
    return(x)
}

load('final_df.Rda')
load("companyLocation.Rda")
flask_url = "http://flask:8080/recommendations"

# Define UI for application that draws a histogram
ui <- dashboardPage(
    skin = "blue",
    dashboardHeader(title = "Job Recommender"),
    dashboardSidebar(
        sidebarMenu(tags$style(HTML(".main-sidebarMenu{width: 300px;}")),
                    menuItem("Recommender", tabName = "Recommender", icon = icon("dashboard")),
                    menuItem("Recommended Job Fiter", tabName = "4", icon = icon('filter'),
                             selectInput(
                                 inputId = "industries",
                                 label = "Industry:",
                                 choices = c("Finance","Healthcare","Supply, Logistics",
                                             "Retail, Marketing","Research","Public Sector","NA") ,
                                 selected = c("Finance","Healthcare","Supply, Logistics",
                                              "Retail, Marketing","Research","Public Sector","NA") ,
                                 multiple = TRUE
                             ),sliderInput(inputId="Salary_range_slider", label = "Salary Range", min = 0,
                                           max = 20000,
                                           value =c(0,20000)
                             )
                    ),
                    menuItem("Trends in Singapore", tabName = "Trends", icon = icon("dashboard"))
        )
    ),dashboardBody(
        tabItems(
            tabItem(tabName = "Recommender",
                    fluidRow(
                        useShinyjs(),
                        extendShinyjs(text = jscode,functions = c("collapse")),
                        box(width = 12, id = "box1",title = "Recommender", status = "primary", solidHeader = TRUE, collapsible = TRUE,
                            selectInput(
                                inputId = "preferredJobTitle",
                                label = "Job Title:",
                                choices = c("data engineer", "business analyst", "data analyst", 
                                            "data scientist", "machine learning engineer"),
                                selected = c("data analyst"),
                                multiple = TRUE
                            ),
                            selectInput(
                                inputId = "JobPortal",
                                label = "Job Portal:",
                                choices = c("indeed", "jobsdb"),
                                multiple = FALSE
                            ),selectInput(
                                inputId = "selectedSkills",
                                label = "Technical Skills You Have:",
                                choices = c("Data Cleaning","MATLAB","R","Python","Go/Golang","Ruby","Perl","Scala",
                                            "Java","C", "C++","Rust","Kotlin","SAS","SPSS","SQL","MySQL","PostgreSQL",
                                            "MongoDB","NoSQL","Machine Learning","Deep Learning","Artificial Intelligence",
                                            "Linear Algebra","Calculus","Statistics","Data Visualization","Microsoft Excel","PowerBI", 
                                            "Tableau","Qlikview","Plotly","D3.js","Apache Spark","Hive","Pig","MapReduce",
                                            "Hadoop","AWS","Amazon S3","Amazon SageMaker","Azure","GCP","Kafka",
                                            "Data Structures and algorithms","MLOps","AutoML","Git","Github","Docker","Airflow",
                                            "MLflow","Kubernetes","Kedro","Neptune","Comet","Kubeflow","Databricks","Wandb",
                                            "API","Linux","UNIX")
                                ,
                                selected = c("R","Python"),
                                multiple = TRUE
                            ),selectInput(
                                inputId = "selectedSoftSkills",
                                label = "Soft Skills You Have:",
                                choices = c("Critical Thinking","Communication","Attention to detail",
                                            "Problem solving","Creativity","Adaptability","Teamwork",
                                            "Leadership","Agile methodology","Project management","Planning")
                                ,selected = c("Critical Thinking","Communication"),
                                multiple = TRUE
                            ),selectInput(
                                inputId = "toAcquireSkills",
                                label = "Technical skills to acquire:",
                                choices = c("Data Cleaning","MATLAB","R","Python","Go/Golang","Ruby","Perl","Scala",
                                            "Java","C", "C++","Rust","Kotlin","SAS","SPSS","SQL","MySQL","PostgreSQL",
                                            "MongoDB","NoSQL","Machine Learning","Deep Learning","Artificial Intelligence",
                                            "Linear Algebra","Calculus","Statistics","Data Visualization","Microsoft Excel","PowerBI", 
                                            "Tableau","Qlikview","Plotly","D3.js","Apache Spark","Hive","Pig","MapReduce",
                                            "Hadoop","AWS","Amazon S3","Amazon SageMaker","Azure","GCP","Kafka",
                                            "Data Structures and algorithms","MLOps","AutoML","Git","Github","Docker","Airflow",
                                            "MLflow","Kubernetes","Kedro","Neptune","Comet","Kubeflow","Databricks","Wandb",
                                            "API","Linux","UNIX")
                                ,
                                selected = c("R","Python"),
                                multiple = TRUE
                            ),selectInput(
                                inputId = "toAcquireSoftSkills",
                                label = "Soft skills to acquire:",
                                choices = c("Critical Thinking","Communication","Attention to detail",
                                            "Problem solving","Creativity","Adaptability",
                                            "Teamwork","Leadership","Agile methodology","Project management","Planning")
                                ,selected = c("Critical Thinking","Communication"),
                                multiple = TRUE
                            ),
                            actionButton("bt1", "Get Recommendations")
                        )
                    ),tabPanel("Recommended Jobs location",
                               leafletOutput("RecommenderMap")
                               
                    ),
                    tabsetPanel(
                        tabPanel("Recommended Jobs",status = "primary",
                                 DT::dataTableOutput("eg_table")
                        )
                    )
            ),tabItem(tabName = "Trends",
                      fluidRow(box(title = "Data science jobs in Sinapore",status = "primary",width = 12, 
                                   solidHeader = TRUE,leafletOutput("map")
                      )
                      ),
                      fluidRow(
                          box(title = "Top Rated Company in Singapore",status = "primary", 
                              solidHeader = TRUE,
                              plotlyOutput("Ratingplot")
                          ),
                          box(title = "Top Paying Company in Singapore",status = "primary", 
                              solidHeader = TRUE,
                              plotlyOutput("companyplot")
                          )
                      )
            )
        )
        
        
    )
)




# Define server logic required to draw a histogram
server <- function(input, output) {
    
    predictions<- eventReactive(input$bt1, {
        current_skills <-unique(c(input$selectedSkills,input$selectedSoftSkills))
        new_skills <-unique(c(input$toAcquireSkills,input$toAcquireSoftSkills))
        list_data<- list(current_skills, new_skills, input$JobPortal,c("",input$preferredJobTitle))
        names(list_data) <- c("current_skills", "new_skills", "job_portal","job_title")
        data <- POST(flask_url, body =  toJSON(list_data,pretty = T, auto_unbox = T),
                     httr::add_headers(`accept` = 'application/json'), 
                     httr::content_type('application/json'))
        list<-fromJSON(content(data,"text"))
        
        list <-lapply(list, nullToNA)
        if(input$JobPortal=="indeed"){
            list<-list[-c(26,27,28,29,30,31)]
        }
        df<-do.call(rbind.data.frame, list)
        recommendations <- as.data.frame(t(df))
        if(input$JobPortal=="jobsdb"){
            recommendations <- recommendations %>%inner_join(.,company_location,by="company") %>%
                rename("Company"="company",
                       "Job_title"="job-title",
                       "Location"="location")%>%
                add_column(Low_salary=NA,High_salary=NA,Industry="NA")
            js$collapse("box1")
            return(recommendations)
            
            
        }else if(input$JobPortal=="indeed"){
            recommendations <-recommendations%>% 
                mutate(Industry=ifelse(Finance==TRUE,"Finance",'')) %>%
                mutate(Industry=ifelse(Healthcare==TRUE,"Healthcare",Industry))%>%
                mutate(Industry=ifelse(`Supply, Logistics`==TRUE,"Supply, Logistics",Industry))%>%
                mutate(Industry=ifelse(`Retail, Marketing`==TRUE,"Retail, Marketing",Industry))%>%
                mutate(Industry=ifelse(Research==TRUE,"Research",Industry))%>%
                mutate(Industry=ifelse(`Public Sector`==TRUE,"Public Sector",Industry)) %>%
                mutate(Industry=ifelse(Industry=="","NA",Industry))
            js$collapse("box1")
            return(recommendations)
        }
        
    })
    
    sub_df <- reactive({
        predictions() %>% 
            filter(Industry %in% input$industries )%>%
            mutate(Salary_range = rowMeans(cbind(as.numeric(Low_salary), as.numeric(High_salary)), na.rm = F))%>%
            filter(between(Salary_range, input$Salary_range_slider[1], 
                           input$Salary_range_slider[2])|is.na(Salary_range))
        
    })
    
    output$map <- renderLeaflet({
        
        df<- final_df%>%mutate(
            url=paste0("<a href='",url,"'>","Apply Now","</a>"),
            pop_up_text = sprintf("<b>%s</b> <br/> %s <br/><b>%s</b>",Job_title,Company,url)
        )
        leaflet(data = df) %>%
            setView(lng = 103.84, 1.35, zoom = 11) %>% 
            addProviderTiles(providers$CartoDB.Positron) %>%
            addMarkers(
                popup = ~as.character(pop_up_text),
            )})
    
    
    output$boxplot <- renderPlotly({
        
        p <- ggplot(sub_df(), aes(y=Salary_range,x=Industry,fill=Industry)) + 
            ylab("Salary range") +
            geom_boxplot()
        ggplotly(p)
    })
    
    output$Ratingplot <- renderPlotly({
        
        p <- final_df %>%filter(Rating<=5)%>%
            select(Company, Rating) %>%
            distinct(Company, Rating)%>%
            top_n(20,Rating)%>%
            ggplot(aes(x = reorder(Company,Rating), y = Rating)) +
            geom_bar(stat="identity",fill="#d9534f")+
            xlab("") +
            ylab("Rating") +
            coord_flip()
        ggplotly(p)
    })
    output$companyplot <- renderPlotly({
        
        p <- final_df %>%
            select(Company, Low_salary, High_salary) %>%
            group_by(Company) %>%
            summarize_if(is.numeric, mean) %>%
            mutate(Mean_salary = rowMeans(cbind(Low_salary, High_salary), na.rm = T),
                   Company = fct_reorder(Company, desc(-Mean_salary))) %>%
            top_n(20, Mean_salary)%>%
            ggplot(aes(x = Company)) +
            geom_point(aes(y = Mean_salary), colour = "blue") +
            geom_linerange(aes(ymin = Low_salary, ymax = High_salary)) +
            geom_hline(aes(yintercept = median(Mean_salary)), lty=2, col='red', alpha = 0.7) +
            ylab("Monthly income") +
            xlab("") +
            coord_flip() +
            theme_bw(base_size = 8)
        ggplotly(p)
    })
    
    
    
    output$eg_table <-DT::renderDataTable({sub_df() %>%
            mutate(Salary_range = rowMeans(cbind(as.numeric(Low_salary), as.numeric(High_salary)), na.rm = F))%>%
            select(Job_title,Company,`Job description`,Salary_range,url)%>%
            mutate(url=paste0("<a href='",url,"'>","Apply Now","</a>"))},
            escape = FALSE,options = list(pageLength = 5,order = list(3, 'desc')),rownames= FALSE)
    
    output$RecommenderMap <- renderLeaflet({
        
        df<- sub_df()%>%mutate(
            url=paste0("<a href='",url,"'>","Apply Now","</a>"),
            pop_up_text = sprintf("<b>%s</b> <br/> %s <br/><b>%s</b>",Job_title, Company,url),
            longitude=as.numeric(longitude),
            latitude=as.numeric(latitude))
        leaflet(data = df) %>%
            setView(lng = 103.84, lat = 1.35, zoom = 11) %>% 
            addProviderTiles(providers$CartoDB.Positron) %>%
            addMarkers(
                popup = ~as.character(pop_up_text)
            )})
    
    
    
}

# Run the application 
shinyApp(ui = ui, server = server)
