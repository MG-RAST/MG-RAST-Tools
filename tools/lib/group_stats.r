group_stats <- function(
                        file_in = "",
                        file_out = "",
                        stat_test = "Kruskal-Wallis", # (an matR stat test)
                        order_by = NULL, # column to order by - integer column index (1 based) or column header -- paste(stat_test, "::fdr", sep="") - NULL is the default behavior - to sort by the fdr.  If you don't know the number of the column you want to sort by - run with default settings first time, figure out the column number, then specify it the second time round. Columns are base 1 indexed.
                        order_decreasing = TRUE,
                        group_lines = 1,           # if groupings are in the file
                        group_line_to_process = 1, # if groupings are in the file
                        my_grouping = NA           # to supply groupings with a list                 
                        )
{

# Check to make sure either that groupings are in the data file, or that a groupings argument
# has been specified


#stop("entry for groupings is not valid - you need group_lines and group_line_to_proces or my_grouping")

  
# Make sure the required pacakges are loaded
  require(matR)
  # require(matlab)
  # require(ggplot2)


#################################### MAIN ##################################
############################################################################
# import groupings from the data file or input arguments
  if ( is.na(my_grouping)[1]==TRUE ){ # if groupings are in the data file, get the one specified in the input args
    groups_raw <- strsplit( x=readLines( con=file_in, n=group_lines ), split="\t" ) 
    my_groups <- groups_raw[[1]][ 2:(length(groups_raw[[1]])) ] # skip first -- should be empty -- field
  }else{
    my_groups <- my_grouping
  }
  #}

# import data
  my_data <- read.table(
                        file_in,
                        header=TRUE,
                        stringsAsFactors=FALSE,
                        sep="\t",
                        comment.char="",
                        quote="",
                        check.names=FALSE,
                        row.names=1,
                        skip=group_lines
                        )

# get dimensions of the data
  my_data.n_rows <- nrow(my_data)
  my_data.n_cols <- ncol(my_data)

# name the groups vector with sample ids from the imported data
  names(my_groups) <- colnames(my_data)

# factor the groups
  my_groups.factor <- factor(my_groups)

# get the levels of the factors (get the list of unique groups)
  my_groups.levels <- levels(factor(my_groups))

# get the number of groups
  num_groups <- nlevels(my_groups.factor)

# perform stat tests (uses sigest from matR)
  my_stats <- sigtest(my_data, my_groups, stat_test)

# Create headers for the data columns
  for (i in 1:dim(my_data)[2]){
    colnames(my_data)[i] <- paste( colnames(my_data)[i], "::", (my_groups)[i], sep="" )
  }
  for (i in 1:dim(my_stats$mean)[2]){
    colnames(my_stats$mean)[i] <- paste( colnames(my_stats$mean)[i], "::group_mean", sep="" )
  }
  for (i in 1:dim(my_stats$sd)[2]){
    colnames(my_stats$sd)[i] <- paste( colnames(my_stats$sd)[i], "::group_sd", sep="" )
  }
  my_stats.statistic <- as.matrix(my_stats$statistic)
  colnames(my_stats.statistic) <- paste(stat_test, "::stat", sep="")
  my_stats.p <- as.matrix(my_stats$p.value)
  colnames(my_stats.p) <- paste(stat_test, "::p", sep="")
  my_stats.fdr <- as.matrix(p.adjust(my_stats$p.value))
  colnames(my_stats.fdr) <- paste(stat_test, "::fdr", sep="")

# generate a summary object - used to generate the plots, and can be used to create a flat file output
  my_stats.summary <- cbind(my_data, my_stats$mean, my_stats$sd, my_stats.statistic, my_stats.p, my_stats.fdr)

  # make sure that order_by value, if other than NULL is supplied, is valid
  if (is.null(order_by)){ # use last column by default, or specified column otherwise
    order_by <- ( ncol(my_stats.summary) )
  } else {
    if (is.integer(order_by)){
      if ( order_by > ncol(my_stats.summary) ){
        stop( paste(
                    "\n\norder_by (", order_by,") must be an integer between 1 and ",
                    ncol(my_stats.summary),
                    " (max number of columns in the output)\n\n",
                    sep="",
                    collaps=""
                    ) )
      }
    }else{
      stop( paste(
                  "\n\norder_by (", order_by,") must be an integer between 1 and ",
                  ncol(my_stats.summary),
                  " (max number of columns in the output)\n\n",
                  sep="",
                  collaps=""
                  ) )
    }
  }
    
  # order the data by the selected column - placing ordered data in a new object
  my_stats.summary.ordered <- my_stats.summary[ order(my_stats.summary[,order_by], decreasing=order_decreasing), ]

# flat file output of the summary file
  write.table(my_stats.summary.ordered, file = file_out, col.names=NA, row.names = rownames(my_stats.summary), sep="\t", quote=FALSE)

}
