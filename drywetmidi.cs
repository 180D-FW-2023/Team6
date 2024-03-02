int[] basicnotes = { 60, 62, 64, 65, 67, 69, 71 };
string[] stringnotes = { "C", "D", "E", "F", "G", "A", "B" };
List<string> remember = new List<string>();
Random r = new Random();
for (int i=0; i!=7; i++){
Console.WriteLine(i);
Directory.CreateDirectory("Path//" + stringnotes[i] + "//");
for(int j=0; j!=929; j++){
var midiFile = new MidiFile();
TempoMap tempoMap = midiFile.GetTempoMap();
var trackChunk = new TrackChunk();
using (var notesManager = trackChunk.ManageNotes()){
NotesCollection notes = notesManager.Notes;
0,
tempoMap)));
notes.Add(new Note(
(SevenBitNumber)basicnotes[i],
LengthConverter.ConvertFrom(
new MetricTimeSpan(hours: 0, minutes: 0,
seconds: 0, milliseconds: r.Next(50,1500)),//Duration
0,
tempoMap),
LengthConverter.ConvertFrom(
new MetricTimeSpan(hours: 0, minutes: 0,
seconds: 0, milliseconds: r.Next(5500,10000)),//Moment of start
0,
tempoMap)));
}
midiFile.Chunks.Add(trackChunk);
midiFile.Write("Path//" + stringnotes[i] + "//" + RandomNonrepeatingString(remember)+".mid");
}
