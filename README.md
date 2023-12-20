Each musical score has its own folder in the "Scores" directory. Each score needs eight files: meter, mscz, mxl, pdf, solo, spos, sposx, and tempo. To create these files for a new score, please follow the steps below:

1. Use the MuseScore app to create a mscz file. Soon from this file, we'll generate three files: mxl, pdf, and spos.

2. Open the mscz file using the MuseScore app, and export a mxl file.

3. Open the mscz file using the MuseScore app, and export a pdf file. Note that one might need to resize the layout (Format -> Page Settings -> Scaling) before exporting.

4. To create a spos file that corresponds with the above pdf file, run something like: `/Applications/MuseScore\ 4.app/Contents/MacOS/mscore myScore.mscz -o myScore.spos`

5. The next step is to generate files that store note, tempo, and meter information. Open musicxml_to_score.py and change the input and output file paths. Run it to generate a few files (.solo, .tempo, and .meter) from the mxl file. The additionally generated .sposx file contains information about the label for each event (which is lacking in the .spox file).