# This is a simple script to calculate the fdr for p values produced from another stat tool
# The output is the input appended with an fdr column
# Rows are sorted by the fdr

mg_calculate_fdr <- function (
                              table_in,                # input data table -- by default, assume that p values are in the last column
                              table_out = "default",   # "default" or an name that the user wants to use for the output
                              p_value_column = "last"  # "last" or 1 based index of selected column
                           )

  {

  ###################################################################################################################################
  # generate filename for the outout
  if ( identical(table_out, "default") ){
    table_out = paste(table_in, ".with_fdr.txt", sep="", collapse="")
  }
  ###################################################################################################################################
    
  data_matrix <- as.matrix(read.table(file=table_in, row.names=1, header=TRUE, sep="\t", colClasses = "character", check.names=FALSE, comment.char = ""))

  n_cols <- ncol(data_matrix)

  if ( identical( p_value_column,"last" )  ){
    fdr_values <- as.matrix(p.adjust( data_matrix[,n_cols], method="fdr"))
  }else{
    if ( p_value_column > n_cols ){
      stop(  paste("Selected column (", p_value_column, ") is greater than the number of columns (",n_cols, ")", sep="" )  )
    }else{
      fdr_values <- as.matrix(p.adjust( data_matrix[,p_value_column], method="fdr"))
    }   
  }

  # add column header to calculated fdr's
  colnames(fdr_values) = "fdr"

  # create matrix with original data and the fdr
  output_matrix <- cbind( data_matrix, fdr_values)

  # sort the output by the fdr
  #output_matrix.ordered <- output_matrix[ order(output_matrix[,ncol(output_matrix)], decreasing=FALSE), ]

  # write the output
  #write.table(output_matrix.ordered, file = table_out, col.names=NA, row.names = rownames(output_matrix.ordered), sep="\t", quote=FALSE)
  write.table(output_matrix, file = table_out, col.names=NA, row.names = rownames(output_matrix), sep="\t", quote=FALSE)
    
  }
