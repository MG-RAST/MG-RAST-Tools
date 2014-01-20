# This is a function that uses matR to generate heatmap-dendrogram vizualizations
# It's a stripped down simple version for basic viz
# pretty much the only user option is to decide if they want the rows labeled
# here's a minimal invocation:
#   plot_mg_heatdend(table_in="test_data.txt")
# here's an invocation that explicitly addresses all of the input args:
#   plot_mg_heatdend(table_in="test_data.txt", image_out="my_heat-dend",label_rows=TRUE, image_width_in=10, image_height_in=10, image_res_dpi=200)

plot_mg_heatdend <<- function(
                          table_in="", # annotation abundance table (raw or normalized values)
                          image_out="default",
                          label_rows=FALSE,
                          order_columns=FALSE,
                          image_width_in=8.5,
                          image_height_in=11,
                          image_res_dpi=300
                          )
  
{
  
  require(matR)

  ###################################################################################################################################
  # generate filename for the image output
  if ( identical(image_out, "default") ){
    image_out = paste(table_in, ".heat-dend.png", sep="", collapse="")
  }else{
    image_out = paste(image_out, ".png", sep="", collapse="")
  }
  ###################################################################################################################################
  
  ###################################################################################################################################
  ######## import/parse all inputs
  
  # import DATA the data (from tab text)
  data_matrix <- data.matrix(read.table(table_in, row.names=1, header=TRUE, sep="\t", comment.char="", quote="", check.names=FALSE))
  # convert data to a matR collection
  data_collection <- suppressWarnings(as(data_matrix, "collection")) # take the input data and create a matR object with it

  ###################################################################################################################################
  # Generate the plot
  png(
      filename = image_out,
      width = image_width_in,
      height = image_height_in,
      res = image_res_dpi,
      units = 'in'
    )
    
  # Can create heat dend with or without row labels
  if ( identical( label_rows, FALSE ) ){
    suppressWarnings(matR::heatmap(data_collection, colsep=NULL, Colv=order_columns))
  }else{
    suppressWarnings(matR::heatmap(data_collection, colsep=NULL, Colv=order_columns, labRow=dimnames(data_collection$x)[[1]]))
  }
  dev.off()

}
