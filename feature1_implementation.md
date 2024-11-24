The global bit map tracks the number of transitions between BB. The trace bit is then iterated through to check back to the global bitmap to see if it already exists. If it does then it ignores it but adds it into the bitmap, if it doesnt that means a new edge is found.

We then save the new edge seed into the queue folder and add it to the seed queue. I saved the filesize and the filename. The filename is based on the amount of files in the directory.

I turned off the print statements so the code can run faster -> more seeds covered which means more crashes.