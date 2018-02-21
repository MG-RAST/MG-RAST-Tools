
######################################################
### Miscellaneous Examples Using the KBase API in R
### Run with:  R CMD BATCH <this_file_name.R>
### Find output in:  <this_file_name.Rout>:
######################################################

library(RJSONIO)
w <- getOption('width')
options(width=120)

######################################################
### simply get a resource and leave as text in JSON format
######################################################
readLines('https://api.mg-rast.org/download/mgm4447943.3?stage=650', warn=FALSE)

######################################################
### get a file resource and save it somewhere
######################################################
download.file('https://api.mg-rast.org/download/mgm4447943.3?file=350.1', destfile = "myfile")

######################################################
### get all project IDs and names
######################################################
p <- fromJSON(readLines('https://api.mg-rast.org/project?limit=0&verbosity=minimal', warn=FALSE),
              asText=TRUE, simplify=FALSE)
projects <- unlist(lapply(p$data, '[[', 'name'))
names(projects) <- lapply(p$data, '[[', 'id')
projects

######################################################
### scrape a skeleton of API documentation
######################################################
resources <- c(
# 'annotation',
  'download',
  'inbox',
  'library',
  'm5nr',
  'matrix',
  'metadata',
  'metagenome',
  'project',
  'sample')
urls <- paste('https://api.mg-rast.org/', resources, sep="")
scrape <- sapply(urls, function (u) fromJSON(readLines(u, warn=FALSE), asText=TRUE, simplify=FALSE), simplify=FALSE)
names(scrape) <- resources
scrape <- unlist(scrape)
scrape [grepl('requests.name|example|description', names(scrape))]

options(width=w)
