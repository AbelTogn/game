from midiutil import MIDIFile

def create_midi():
    # Création d'un objet MIDIFile avec 2 pistes
    midi = MIDIFile(2)

    # Paramètres globaux
    tempo = 120  # Tempo en BPM
    volume = 100  # Volume (0-127)

    # Piste 1 : Accords
    track = 0
    channel = 0
    time = 0  # Temps en battements

    midi.addTempo(track, time, tempo)
    
    # Liste d'accords
    chords = [[60, 64, 67], [62, 65, 69], [64, 67, 71], [65, 69, 72]]

    chord_duration = 2  # Durée des accords en battements
    
    # Ajout des accords
    for _ in range(2):  # Répète la séquence d'accords deux fois
        for chord in chords:
            for note in chord:
                midi.addNote(track, channel, note, time, chord_duration, volume)
            time += chord_duration

    # Piste 2 : Mélodie
    track = 1
    channel = 1
    time = 0  # Réinitialisation du temps

    midi.addTempo(track, time, tempo)
    
    # Séquence de notes pour la mélodie
    melody_notes = [[60, 62, 64, 65, 67, 69, 71, 72],  # Première séquence
                    [62, 64, 65, 67, 69, 71, 72, 74]]  # Deuxième séquence
    melody_duration = 0.5  # Durée des notes en battements
    
    # Ajout de la mélodie
    for sequence in melody_notes:
        for note in sequence:
            midi.addNote(track, channel, note, time, melody_duration, volume)
            time += melody_duration

    # Enregistrement du fichier MIDI
    with open("output.mid", "wb") as midi_file:
        midi.writeFile(midi_file)

if __name__ == "__main__":
    create_midi()
