* Cremat model libraries referenced by cr200_1us.sub / cr210.sub.
* LTspice resolves these from its own lib dir (UniversalOpAmp2.lib, standard.jft, LTC.lib).
* Included once at the top of every top-level deck.
.lib UniversalOpAmp2.lib
.model NJF NJF
.model PJF PJF
.lib C:\Users\darro\AppData\Local\LTspice\lib\cmp\standard.jft
.lib LTC.lib
