// UI Elements
const tableBody = document.getElementById('table-body');
const addRowBtn = document.getElementById('add-row-btn');
const clearTableBtn = document.getElementById('clear-table-btn');
const runPipelineBtn = document.getElementById('run-pipeline-btn');

// Editor Tabs and Elements (JSON and CSV)
const tabTable = document.getElementById('tab-table');
const tabJson = document.getElementById('tab-json');
const tabCsv = document.getElementById('tab-csv');
const tableViewContainer = document.getElementById('table-view-container');
const jsonEditorContainer = document.getElementById('json-editor-container');
const csvEditorContainer = document.getElementById('csv-editor-container');
const rawJsonEditor = document.getElementById('raw-json-editor');
const rawCsvEditor = document.getElementById('raw-csv-editor');
const jsonValidationError = document.getElementById('json-validation-error');
const csvValidationError = document.getElementById('csv-validation-error');
let currentView = 'table';

// Custom Preset Management & Import/Export Elements
const userPresetsSelect = document.getElementById('user-presets-select');
const savePresetBtn = document.getElementById('save-preset-btn');
const deletePresetBtn = document.getElementById('delete-preset-btn');
const importJsonBtn = document.getElementById('import-json-btn');
const exportJsonBtn = document.getElementById('export-json-btn');
const importFileInput = document.getElementById('import-file-input');

const importCsvBtn = document.getElementById('import-csv-btn');
const exportCsvBtn = document.getElementById('export-csv-btn');
const importCsvInput = document.getElementById('import-csv-input');

const welcomeView = document.getElementById('welcome-view');
const loadingView = document.getElementById('loading-view');
const errorView = document.getElementById('error-view');
const outputView = document.getElementById('output-view');
const errorMessage = document.getElementById('error-message');
const errorDismissBtn = document.getElementById('error-dismiss-btn');

const pdfViewer = document.getElementById('pdf-viewer');
const audioPlayer = document.getElementById('audio-player');
const audioPlayerPerc = document.getElementById('audio-player-perc');
const videoPlayer = document.getElementById('video-player');

const downloadPdf = document.getElementById('download-pdf');
const downloadLy = document.getElementById('download-ly');
const downloadWav = document.getElementById('download-wav');
const downloadSf2 = document.getElementById('download-sf2');
const downloadMidiVocal = document.getElementById('download-midi-vocal');
const downloadMidiRaw = document.getElementById('download-midi-raw');
const downloadWavPerc = document.getElementById('download-wav-perc');
const downloadMidiPerc = document.getElementById('download-midi-perc');
const downloadVideo = document.getElementById('download-video');

// Presets Data Cache (Dynamically populated from static/presets)
let PRESETS = {};

// Event List Array (Initial State)
let events = [
    { foot: 'left', note_length: 4, lyric: 'kick', comment: 'basic' },
    { foot: 'right', note_length: 4, lyric: 'step', comment: 'basic' },
    { foot: 'left', note_length: 4, lyric: 'tap', comment: 'sync' },
    { foot: 'right', note_length: 4, lyric: 'stomp', comment: 'downbeat' }
];

// Initialize UI
window.addEventListener('DOMContentLoaded', () => {
    renderTable();
    
    // Wire control buttons
    addRowBtn.addEventListener('click', () => addRow());
    clearTableBtn.addEventListener('click', () => clearTable());
    runPipelineBtn.addEventListener('click', () => runPipeline());
    errorDismissBtn.addEventListener('click', () => showView('welcome'));

    // Load dynamic presets from subdirectory
    initializePresets();

    // Wire raw view toggles
    tabTable.addEventListener('click', () => switchEditorView('table'));
    tabJson.addEventListener('click', () => switchEditorView('json'));
    tabCsv.addEventListener('click', () => switchEditorView('csv'));

    // Preset management triggers
    savePresetBtn.addEventListener('click', () => savePresetToBrowser());
    deletePresetBtn.addEventListener('click', () => deletePresetFromBrowser());
    userPresetsSelect.addEventListener('change', (e) => loadUserPreset(e.target.value));

    // File import/export triggers
    exportJsonBtn.addEventListener('click', () => exportSequence());
    importJsonBtn.addEventListener('click', () => importFileInput.click());
    importFileInput.addEventListener('change', (e) => handleFileImport(e));

    exportCsvBtn.addEventListener('click', () => exportCSVSequence());
    importCsvBtn.addEventListener('click', () => importCsvInput.click());
    importCsvInput.addEventListener('change', (e) => handleCSVImport(e));

    // Initial load of custom presets
    loadSavedPresetsList();
});

// Render the entire table based on internal events array
function renderTable() {
    tableBody.innerHTML = '';
    events.forEach((event, index) => {
        createTableRow(event, index);
    });
}

// Create a single row HTML element and inject into the table
function createTableRow(event, index) {
    const row = document.createElement('tr');
    row.className = 'row-anim';
    row.innerHTML = `
        <td><span class="row-index">${index + 1}</span></td>
        <td>
            <select class="input-control foot-select">
                <option value="left" ${event.foot === 'left' ? 'selected' : ''}>Left Foot</option>
                <option value="right" ${event.foot === 'right' ? 'selected' : ''}>Right Foot</option>
                <option value="rest" ${event.foot === 'rest' ? 'selected' : ''}>Rest (Silence)</option>
            </select>
        </td>
        <td>
            <input type="text" class="input-control length-input" list="note-lengths" value="${event.note_length || '4'}" placeholder="e.g. 4.">
        </td>
        <td>
            <input type="text" class="input-control lyric-input" placeholder="e.g. kick" value="${event.lyric || ''}" ${event.foot === 'rest' ? 'disabled' : ''}>
        </td>
        <td>
            <input type="text" class="input-control comment-input" placeholder="e.g. charleston" value="${event.comment || ''}" ${event.foot === 'rest' ? 'disabled' : ''}>
        </td>
        <td style="text-align: center;">
            <button class="btn-delete" title="Delete Event">✕</button>
        </td>
    `;

    // Hook inputs to update state directly when edited
    const footSelect = row.querySelector('.foot-select');
    const lengthInput = row.querySelector('.length-input');
    const lyricInput = row.querySelector('.lyric-input');
    const commentInput = row.querySelector('.comment-input');
    const deleteBtn = row.querySelector('.btn-delete');

    footSelect.addEventListener('change', (e) => {
        const val = e.target.value;
        events[index].foot = val;
        if (val === 'rest') {
            lyricInput.value = '';
            lyricInput.disabled = true;
            commentInput.value = '';
            commentInput.disabled = true;
            events[index].lyric = '';
            events[index].comment = '';
        } else {
            lyricInput.disabled = false;
            commentInput.disabled = false;
        }
    });

    lengthInput.addEventListener('input', (e) => {
        events[index].note_length = e.target.value;
    });

    lyricInput.addEventListener('input', (e) => {
        events[index].lyric = e.target.value;
    });

    commentInput.addEventListener('input', (e) => {
        events[index].comment = e.target.value;
    });

    deleteBtn.addEventListener('click', () => {
        deleteRow(index);
    });

    tableBody.appendChild(row);
}

// Add a new row to state and view
function addRow() {
    // Default values reflect preceding row if available, else standard quarter note left
    let defaultRow = { foot: 'left', note_length: 4, lyric: '', comment: '' };
    if (events.length > 0) {
        const lastRow = events[events.length - 1];
        defaultRow.foot = lastRow.foot === 'left' ? 'right' : 'left'; // Alternate feet
        defaultRow.note_length = lastRow.note_length;
    }
    events.push(defaultRow);
    renderTable();
    
    // Auto-scroll table container to bottom to track additions
    const container = document.querySelector('.table-container');
    container.scrollTop = container.scrollHeight;
}

// Delete row from state and view
function deleteRow(index) {
    events.splice(index, 1);
    renderTable();
}

// Clear all rows
function clearTable() {
    events = [];
    renderTable();
    if (currentView === 'json') {
        rawJsonEditor.value = '[]';
        jsonValidationError.classList.add('hidden');
    } else if (currentView === 'csv') {
        rawCsvEditor.value = 'foot,note_length,lyric,comment\n';
        csvValidationError.classList.add('hidden');
    }
}

// Load a preset sequence (with dynamic lazy-loading from server subdirectory)
async function loadPreset(key) {
    if (!PRESETS[key]) {
        try {
            const response = await fetch(`/presets/${key}.json`);
            if (!response.ok) throw new Error(`Status: ${response.status}`);
            const data = await response.json();
            PRESETS[key] = data;
        } catch (err) {
            alert(`Failed to load preset "${key}": ${err.message}`);
            return;
        }
    }
    
    events = JSON.parse(JSON.stringify(PRESETS[key])); // deep copy
    renderTable();
    if (currentView === 'json') {
        rawJsonEditor.value = JSON.stringify(events, null, 4);
        jsonValidationError.classList.add('hidden');
    } else if (currentView === 'csv') {
        rawCsvEditor.value = generateCSVString(events);
        csvValidationError.classList.add('hidden');
    }
    showView('welcome');
}

// Helper to toggle visible cards
function showView(view) {
    welcomeView.classList.add('hidden');
    loadingView.classList.add('hidden');
    errorView.classList.add('hidden');
    outputView.classList.add('hidden');

    if (view === 'welcome') welcomeView.classList.remove('hidden');
    else if (view === 'loading') loadingView.classList.remove('hidden');
    else if (view === 'error') errorView.classList.remove('hidden');
    else if (view === 'output') outputView.classList.remove('hidden');
}

// Simulate stage highlights during loading
const stages = ['stage-lilypond', 'stage-tts', 'stage-sf2', 'stage-midi', 'stage-render'];

function setStageStatus(stageId, status, icon) {
    const el = document.getElementById(stageId);
    if (!el) return;
    
    el.className = 'stage';
    el.querySelector('.stage-status').innerText = icon;
    
    if (status === 'active') {
        el.classList.add('active');
    } else if (status === 'success') {
        el.classList.add('success');
    }
}

function resetPipelineStages() {
    stages.forEach(s => setStageStatus(s, 'pending', '⏳'));
}

// Run the full synthesizer pipeline API
async function runPipeline() {
    if (currentView === 'json') {
        if (!syncJsonToTable()) {
            alert("Please fix JSON validation errors before running the pipeline!");
            return;
        }
    } else if (currentView === 'csv') {
        if (!syncCsvToTable()) {
            alert("Please fix CSV validation errors before running the pipeline!");
            return;
        }
    }

    if (events.length === 0) {
        alert("Please add at least one event row to synthesize!");
        return;
    }

    showView('loading');
    resetPipelineStages();

    // Stage 1 active (LilyPond start)
    setStageStatus('stage-lilypond', 'active', '⚙️');

    // Fake pipeline progress increments so users feel the step-by-step nature of compiled blocks
    const t1 = setTimeout(() => {
        setStageStatus('stage-lilypond', 'success', '🟢');
        setStageStatus('stage-tts', 'active', '⚙️');
    }, 1200);

    const t2 = setTimeout(() => {
        setStageStatus('stage-tts', 'success', '🟢');
        setStageStatus('stage-sf2', 'active', '⚙️');
    }, 2800);

    try {
        const response = await fetch('/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(events)
        });

        // Clear timers so they don't fight with final actual outcome
        clearTimeout(t1);
        clearTimeout(t2);

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || "Network error compiling assets.");
        }

        // Complete remaining stages rapidly on server success
        stages.forEach(s => setStageStatus(s, 'success', '🟢'));

        // Delay slightly before showing output so the user registers the successful checks
        setTimeout(() => {
            // Populate output UI elements
            pdfViewer.src = result.files.pdf;
            
            // Reload audio tags to play fresh files
            audioPlayer.src = result.files.audio;
            audioPlayer.load();

            audioPlayerPerc.src = result.files.audio_perc;
            audioPlayerPerc.load();

            // Load video player source
            videoPlayer.src = result.files.video;
            videoPlayer.load();

            // Set download hrefs
            downloadPdf.href = result.files.pdf;
            downloadLy.href = result.files.ly;
            downloadWav.href = result.files.audio;
            downloadSf2.href = result.files.soundfont;
            downloadMidiVocal.href = result.files.midi_vocal;
            downloadMidiRaw.href = result.files.midi_raw;
            downloadWavPerc.href = result.files.audio_perc;
            downloadMidiPerc.href = result.files.midi_perc;
            downloadVideo.href = result.files.video;

            showView('output');
        }, 800);

    } catch (err) {
        clearTimeout(t1);
        clearTimeout(t2);
        
        stages.forEach(s => setStageStatus(s, 'error', '🔴'));
        errorMessage.innerText = err.message || err;
        showView('error');
    }
}

// Custom Preset Management Operations
function getStoredPresets() {
    try {
        const stored = localStorage.getItem('sf_presets');
        return stored ? JSON.parse(stored) : {};
    } catch (e) {
        console.error("Failed to parse stored presets:", e);
        return {};
    }
}

function loadSavedPresetsList(selectName = "") {
    // Clear dynamic options (everything except the placeholder)
    userPresetsSelect.innerHTML = '<option value="" disabled selected>Load Saved Preset...</option>';
    
    const presets = getStoredPresets();
    const sortedNames = Object.keys(presets).sort();
    
    sortedNames.forEach(name => {
        const opt = document.createElement('option');
        opt.value = name;
        opt.innerText = name;
        if (name === selectName) {
            opt.selected = true;
        }
        userPresetsSelect.appendChild(opt);
    });

    // Toggle delete button based on whether a preset is currently selected
    deletePresetBtn.disabled = !selectName;
}

function savePresetToBrowser() {
    // Sync editor first if in text editor views
    if (currentView === 'json') {
        if (!syncJsonToTable()) {
            alert("Please fix JSON validation errors before saving!");
            return;
        }
    } else if (currentView === 'csv') {
        if (!syncCsvToTable()) {
            alert("Please fix CSV validation errors before saving!");
            return;
        }
    }

    if (events.length === 0) {
        alert("Cannot save an empty sequence!");
        return;
    }

    const name = prompt("Enter a name for this custom preset:");
    if (!name) return; // cancelled or empty

    const cleanName = name.trim();
    if (!cleanName) return;

    const presets = getStoredPresets();
    presets[cleanName] = JSON.parse(JSON.stringify(events));
    
    localStorage.setItem('sf_presets', JSON.stringify(presets));
    loadSavedPresetsList(cleanName);
    alert(`Preset "${cleanName}" saved successfully!`);
}

function loadUserPreset(name) {
    const presets = getStoredPresets();
    if (presets[name]) {
        events = JSON.parse(JSON.stringify(presets[name]));
        renderTable();
        
        if (currentView === 'json') {
            rawJsonEditor.value = JSON.stringify(events, null, 4);
            jsonValidationError.classList.add('hidden');
        } else if (currentView === 'csv') {
            rawCsvEditor.value = generateCSVString(events);
            csvValidationError.classList.add('hidden');
        }
        
        deletePresetBtn.disabled = false;
        showView('welcome');
    }
}

function deletePresetFromBrowser() {
    const activePreset = userPresetsSelect.value;
    if (!activePreset) return;

    if (confirm(`Are you sure you want to delete preset "${activePreset}"?`)) {
        const presets = getStoredPresets();
        delete presets[activePreset];
        localStorage.setItem('sf_presets', JSON.stringify(presets));
        loadSavedPresetsList();
    }
}

// File Import/Export Operations
function exportSequence() {
    // Sync editor first if in text editor views
    if (currentView === 'json') {
        if (!syncJsonToTable()) {
            alert("Please fix JSON validation errors before exporting!");
            return;
        }
    } else if (currentView === 'csv') {
        if (!syncCsvToTable()) {
            alert("Please fix CSV validation errors before exporting!");
            return;
        }
    }

    if (events.length === 0) {
        alert("Cannot export an empty sequence!");
        return;
    }

    const jsonStr = JSON.stringify(events, null, 4);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = 'sequence.json';
    document.body.appendChild(a);
    a.click();
    
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function handleFileImport(e) {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = function(evt) {
        try {
            const parsed = JSON.parse(evt.target.result);
            if (!Array.isArray(parsed)) {
                throw new Error("JSON root must be an array.");
            }
            
            // Basic schema check
            for (let i = 0; i < parsed.length; i++) {
                const ev = parsed[i];
                if (typeof ev !== 'object' || ev === null) {
                    throw new Error(`Event at index ${i} is not a valid object.`);
                }
                if (!ev.foot) {
                    throw new Error(`Event at index ${i} is missing required "foot" parameter.`);
                }
                ev.note_length = ev.note_length !== undefined ? String(ev.note_length) : "4";
                ev.lyric = ev.lyric !== undefined ? String(ev.lyric) : "";
                ev.comment = ev.comment !== undefined ? String(ev.comment) : "";
            }
            
            events = parsed;
            renderTable();
            
            if (currentView === 'json') {
                rawJsonEditor.value = JSON.stringify(events, null, 4);
                jsonValidationError.classList.add('hidden');
            } else if (currentView === 'csv') {
                rawCsvEditor.value = generateCSVString(events);
                csvValidationError.classList.add('hidden');
            }
            
            userPresetsSelect.selectedIndex = 0;
            deletePresetBtn.disabled = true;
            
            showView('welcome');
            alert("Sequence imported successfully!");
            
        } catch (err) {
            alert(`Import Failed: ${err.message}`);
        } finally {
            importFileInput.value = ''; // Reset input to allow re-importing the same file
        }
    };
    reader.readAsText(file);
}

function handleCSVImport(e) {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = function(evt) {
        try {
            const text = evt.target.result;
            const parsed = parseCSV(text);
            
            events = parsed;
            renderTable();
            
            if (currentView === 'json') {
                rawJsonEditor.value = JSON.stringify(events, null, 4);
                jsonValidationError.classList.add('hidden');
            } else if (currentView === 'csv') {
                rawCsvEditor.value = generateCSVString(events);
                csvValidationError.classList.add('hidden');
            }
            
            userPresetsSelect.selectedIndex = 0;
            deletePresetBtn.disabled = true;
            
            showView('welcome');
            alert("Sequence imported successfully from CSV!");
            
        } catch (err) {
            alert(`CSV Import Failed: ${err.message}`);
        } finally {
            importCsvInput.value = ''; // Reset input to allow re-importing the same file
        }
    };
    reader.readAsText(file);
}

function parseCSV(text) {
    const lines = text.split(/\r?\n/);
    if (lines.length === 0 || !lines[0].trim()) {
        throw new Error("CSV file is empty.");
    }
    
    // Parse header row
    const headers = parseCSVLine(lines[0]);
    const footIndex = headers.findIndex(h => h.toLowerCase() === 'foot');
    const noteLengthIndex = headers.findIndex(h => h.toLowerCase() === 'note_length');
    const lyricIndex = headers.findIndex(h => h.toLowerCase() === 'lyric');
    const commentIndex = headers.findIndex(h => h.toLowerCase() === 'comment');
    
    if (footIndex === -1) {
        throw new Error("CSV must contain a 'foot' column.");
    }
    
    const parsedEvents = [];
    for (let i = 1; i < lines.length; i++) {
        const line = lines[i].trim();
        if (!line) continue; // Skip empty lines
        
        const values = parseCSVLine(line);
        if (values.length === 0) continue;
        
        // Pad values array if it's shorter than headers
        while (values.length < headers.length) {
            values.push('');
        }
        
        const event = {
            foot: values[footIndex] ? values[footIndex].toLowerCase() : 'left',
            note_length: noteLengthIndex !== -1 && values[noteLengthIndex] ? values[noteLengthIndex] : '4',
            lyric: lyricIndex !== -1 && values[lyricIndex] ? values[lyricIndex] : '',
            comment: commentIndex !== -1 && values[commentIndex] ? values[commentIndex] : ''
        };
        
        // Normalize foot
        if (event.foot !== 'left' && event.foot !== 'right' && event.foot !== 'rest') {
            event.foot = 'left';
        }
        parsedEvents.push(event);
    }
    return parsedEvents;
}

function parseCSVLine(line) {
    const result = [];
    let current = '';
    let inQuotes = false;
    for (let i = 0; i < line.length; i++) {
        const char = line[i];
        if (char === '"') {
            inQuotes = !inQuotes;
        } else if (char === ',' && !inQuotes) {
            result.push(current);
            current = '';
        } else {
            current += char;
        }
    }
    result.push(current);
    return result.map(v => {
        let clean = v.trim();
        if (clean.startsWith('"') && clean.endsWith('"')) {
            clean = clean.substring(1, clean.length - 1).trim();
        }
        return clean;
    });
}

function exportCSVSequence() {
    if (currentView === 'json') {
        if (!syncJsonToTable()) {
            alert("Please fix JSON validation errors before exporting!");
            return;
        }
    } else if (currentView === 'csv') {
        if (!syncCsvToTable()) {
            alert("Please fix CSV validation errors before exporting!");
            return;
        }
    }

    if (events.length === 0) {
        alert("Cannot export an empty sequence!");
        return;
    }

    // Header row
    let csvContent = "foot,note_length,lyric,comment\n";
    
    // Data rows
    events.forEach(ev => {
        const foot = ev.foot || 'left';
        const noteLength = ev.note_length || '4';
        
        // Escape quotes and wrap in quotes if contains commas or quotes
        const formatField = (field) => {
            const str = String(field || '');
            if (str.includes(',') || str.includes('"') || str.includes('\n')) {
                return `"${str.replace(/"/g, '""')}"`;
            }
            return str;
        };
        
        const lyric = formatField(ev.lyric);
        const comment = formatField(ev.comment);
        
        csvContent += `${foot},${noteLength},${lyric},${comment}\n`;
    });

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = 'sequence.csv';
    document.body.appendChild(a);
    a.click();
    
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// View Switching and Validation
function switchEditorView(view) {
    if (view === currentView) return;

    // Sync current active editor back to events table first
    if (currentView === 'json') {
        if (!syncJsonToTable()) return;
    } else if (currentView === 'csv') {
        if (!syncCsvToTable()) return;
    }

    // Deactivate all tab selectors and hide all pane containers
    tabTable.classList.remove('active');
    tabJson.classList.remove('active');
    tabCsv.classList.remove('active');
    
    tableViewContainer.classList.add('hidden');
    jsonEditorContainer.classList.add('hidden');
    csvEditorContainer.classList.add('hidden');

    if (view === 'json') {
        rawJsonEditor.value = JSON.stringify(events, null, 4);
        jsonValidationError.classList.add('hidden');
        jsonEditorContainer.classList.remove('hidden');
        tabJson.classList.add('active');
        
        addRowBtn.classList.add('hidden');
        clearTableBtn.classList.add('hidden');
        currentView = 'json';
    } else if (view === 'csv') {
        rawCsvEditor.value = generateCSVString(events);
        csvValidationError.classList.add('hidden');
        csvEditorContainer.classList.remove('hidden');
        tabCsv.classList.add('active');
        
        addRowBtn.classList.add('hidden');
        clearTableBtn.classList.add('hidden');
        currentView = 'csv';
    } else {
        tableViewContainer.classList.remove('hidden');
        tabTable.classList.add('active');
        
        addRowBtn.classList.remove('hidden');
        clearTableBtn.classList.remove('hidden');
        currentView = 'table';
    }
}

function syncJsonToTable() {
    try {
        const parsed = JSON.parse(rawJsonEditor.value);
        if (!Array.isArray(parsed)) {
            throw new Error("JSON root must be an array of events.");
        }
        // Basic validation of fields
        for (let i = 0; i < parsed.length; i++) {
            const ev = parsed[i];
            if (typeof ev !== 'object' || ev === null) {
                throw new Error(`Event at index ${i} is not a valid object.`);
            }
            if (!ev.foot) {
                throw new Error(`Event at index ${i} is missing the "foot" field.`);
            }
            // Normalize note_length to string
            if (ev.note_length !== undefined) {
                ev.note_length = String(ev.note_length);
            } else {
                ev.note_length = "4";
            }
            ev.lyric = ev.lyric !== undefined ? String(ev.lyric) : "";
            ev.comment = ev.comment !== undefined ? String(ev.comment) : "";
        }
        
        events = parsed;
        renderTable();
        jsonValidationError.classList.add('hidden');
        return true;
    } catch (err) {
        jsonValidationError.innerText = `⚠️ JSON Parse Error: ${err.message}`;
        jsonValidationError.classList.remove('hidden');
        return false;
    }
}

function syncCsvToTable() {
    try {
        const parsed = parseCSV(rawCsvEditor.value);
        events = parsed;
        renderTable();
        csvValidationError.classList.add('hidden');
        return true;
    } catch (err) {
        csvValidationError.innerText = `⚠️ CSV Parse Error: ${err.message}`;
        csvValidationError.classList.remove('hidden');
        return false;
    }
}

function generateCSVString(eventList) {
    let csvContent = "foot,note_length,lyric,comment\n";
    eventList.forEach(ev => {
        const foot = ev.foot || 'left';
        const noteLength = ev.note_length || '4';
        
        const formatField = (field) => {
            const str = String(field || '');
            if (str.includes(',') || str.includes('"') || str.includes('\n')) {
                return `"${str.replace(/"/g, '""')}"`;
            }
            return str;
        };
        
        const lyric = formatField(ev.lyric);
        const comment = formatField(ev.comment);
        
        csvContent += `${foot},${noteLength},${lyric},${comment}\n`;
    });
    return csvContent;
}

// Preset Resolver Utilities
async function initializePresets() {
    try {
        const response = await fetch('/presets');
        if (!response.ok) throw new Error(`Status: ${response.status}`);
        const keys = await response.json();
        
        const container = document.getElementById('preset-buttons-container');
        if (!container) return;
        container.innerHTML = '';
        
        keys.forEach(key => {
            const btn = document.createElement('button');
            btn.className = 'btn btn-secondary btn-sm';
            
            // Format name nicely
            let label = formatPresetName(key);
            if (key === 'dance') label = 'Dance Routine';
            else if (key === 'balboa') label = 'Balboa Preset';
            
            btn.innerText = label;
            btn.addEventListener('click', () => loadPreset(key));
            container.appendChild(btn);
        });
    } catch (err) {
        console.error("Failed to load dynamic presets:", err);
    }
}

function formatPresetName(key) {
    return key.split('-').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
}
