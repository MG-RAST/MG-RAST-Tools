rename_columns <- function(
                           data_table = "~/temp/my_data.txt",
                           metadata_table = "~/temp/my_metadata.txt",
                           table_out="default",
                           metadata_oldName_col=0, # 0 based index of metadata column with current column names of the data table (0 is default - row names column of data_table)
                           metadata_newName_col=1  # 0 based index of metadata column with new names
                           )

  {
  # generate name for the output file
    if ( identical(table_out, "default") ){
      table_out = paste(data_table, ".col_renamed.txt", sep="", collapse="")
    }else{
      table_out = paste(data_table, ".txt", sep="", collapse="")
    }

######## import/parse all inputs
# import DATA the data (from tab text)
    data_matrix <<- data.matrix(read.table(data_table, row.names=1, header=TRUE, sep="\t", comment.char="", quote="", check.names=FALSE))

    metadata_matrix <<- as.matrix(read.table(file=metadata_table, row.names=1, header=TRUE, sep="\t", colClasses = "character", check.names=FALSE, comment.char = ""))

    if ( dim(data_matrix)[2] != dim(metadata_matrix)[1] ){
      paste(
            "The number of data columns (",
            dim(data_matrix)[2],
            ") does not match the number of rows (",
            dim(metadata_matrix)[1],
            ") in the metadata file",
            sep="",
            collapse="")
      stop
    }
    
    names_list <<- as.vector(  metadata_matrix[ , metadata_newName_col] )
    if( metadata_oldName_col==0 ){
      names(names_list) <<- rownames(metadata_matrix)
    }else{
      names(names_list) <<- metadata_matrix[,metadata_oldName_col]
    }

    print("made it here")
    new_matrix <- data_matrix

    colnames(new_matrix)
    
    for (i in  1:dim(data_matrix)[2]){ 
      
      current_name <- colnames(new_matrix)[i]
      new_name <- names_list[ current_name ]
      colnames(new_matrix)[i] <- new_name
    }

    write.table(new_matrix, file = table_out, sep = "\t", col.names=NA, row.names = TRUE, quote=FALSE)

  }

