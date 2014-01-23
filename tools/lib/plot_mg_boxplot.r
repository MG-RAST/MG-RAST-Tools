# This is a function that uses matR to generate boxplot vizualizations
# It's a stripped down simple version for basic viz
# pretty much the only user option is to decide if they want the rows labeled
# here's a minimal invocation:
#   plot_mg_boxplot(table_in="test_data.txt")
# here's an invocation that explicitly addresses all of the input args:
#   plot_mg_boxplot(table_in="test_data.txt", image_out="my_boxplot",label_rows=TRUE, image_width_in=10, image_height_in=10, image_res_dpi=200)

plot_mg_boxplot <<- function(
                          table_in="", # annotation abundance table (raw or normalized values)
                          image_out="default",
                          label_rows=FALSE,
                          label_cex=0.1,
                          image_width_in=10.5,
                          image_height_in=8,
                          image_res_dpi=150
                          )
  
{
  
  require(matR)

  ###################################################################################################################################
  # generate filename for the image output
  if ( identical(image_out, "default") ){
    image_out = paste(table_in, ".boxplot.png", sep="", collapse="")
  }else{
    image_out = paste(image_out, ".png", sep="", collapse="")
  }
  ###################################################################################################################################
  
  ###################################################################################################################################
  ######## import/parse all inputs
  
  # import DATA the data (from tab text)
  data_matrix <- data.matrix(read.table(table_in, row.names=1, header=TRUE, sep="\t", comment.char="", quote="", check.names=FALSE))
  
  ###################################################################################################################################
  # Generate the plot
  png(
      filename = image_out,
      width = image_width_in,
      height = image_height_in,
      res = image_res_dpi,
      units = 'in'
    )

  # create a boxplot
  boxplot(data_matrix, las=2, mar = c(3, 0.5, 0.5, 0.5), cex.lab=label_cex )
  #boxplot(data_matrix, las=2, mai = c(3, 0.5, 0.5, 0.5), cex.lab=label_cex )
  dev.off()

}
