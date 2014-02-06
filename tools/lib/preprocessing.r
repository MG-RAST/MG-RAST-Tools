MGRAST_preprocessing <<- function(
                                  file_in,     # name of the input file (tab delimited text with the raw counts)
                                  file_out = "preprocessed_data",    # name of the output data file (tab delimited text of preprocessed data)
                                  remove_sg = FALSE, # boolean to remove singleton counts
                                  sg_threshold = 1 # rows with a sum of counts equal to or less than this value will be removed if remove_sg=TRUE
                                  )
  {

 
# Sub to remove singletons
    remove.singletons <- function (x, lim.entry = sg_threshold, lim.row = sg_threshold, ...) {
      x <- as.matrix (x)
      x [is.na (x)] <- 0
      x [x <= lim.entry] <- 0
      x [apply (x, MARGIN = 1, sum) >= lim.row, ]
    }
   
# functiona that performs normalization (log transformation, standardization, scaling fro m 0 to 1)
    normalize <- function (x, method = c("standard"), ...) {
      method <- match.arg(method)
      x <- as.matrix(x)
      x[is.na(x)] <- 0
      x <- log2(x + 1)
      mu <- matrix(apply(x, 2, mean), nr = nrow(x), nc = ncol(x),
                   byrow = TRUE)
      sigm <- apply(x, 2, sd)
      sigm <- matrix(ifelse(sigm == 0, 1, sigm), nr = nrow(x),
                     nc = ncol(x), byrow = TRUE)
      x <- (x - mu)/sigm
      shift <- min(x, na.rm = TRUE)
      scale <- max(x, na.rm = TRUE) - shift
      if (scale != 0) x <- (x - shift)/scale
      x
    }
   
###### MAIN
### Input the data
    input_data = data.matrix(read.table(file_in, row.names=1, header=TRUE, sep="\t", comment.char="", quote=""))
   
### remove singletons
    if(remove_sg==TRUE){
      input_data <- remove.singletons(x=input_data)
    }
   
### Norm, standardize, and scale the data
    input_data <- normalize(x=input_data)

###### write the log transformed and centered data to a file
    write.table(input_data, file=file_out, sep="\t", col.names = NA, row.names = TRUE, quote = FALSE)
  }
