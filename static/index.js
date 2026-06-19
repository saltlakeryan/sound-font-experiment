// UI Elements
const tableBody = document.getElementById('table-body');
const addRowBtn = document.getElementById('add-row-btn');
const clearTableBtn = document.getElementById('clear-table-btn');
const runPipelineBtn = document.getElementById('run-pipeline-btn');

// Raw JSON Editor Tabs and Elements
const tabTable = document.getElementById('tab-table');
const tabJson = document.getElementById('tab-json');
const tableViewContainer = document.getElementById('table-view-container');
const jsonEditorContainer = document.getElementById('json-editor-container');
const rawJsonEditor = document.getElementById('raw-json-editor');
const jsonValidationError = document.getElementById('json-validation-error');
let currentView = 'table';

const welcomeView = document.getElementById('welcome-view');
const loadingView = document.getElementById('loading-view');
const errorView = document.getElementById('error-view');
const outputView = document.getElementById('output-view');
const errorMessage = document.getElementById('error-message');
const errorDismissBtn = document.getElementById('error-dismiss-btn');

const pdfViewer = document.getElementById('pdf-viewer');
const audioPlayer = document.getElementById('audio-player');

const downloadPdf = document.getElementById('download-pdf');
const downloadWav = document.getElementById('download-wav');
const downloadSf2 = document.getElementById('download-sf2');
const downloadMidiVocal = document.getElementById('download-midi-vocal');
const downloadMidiRaw = document.getElementById('download-midi-raw');

// Preset Buttons
const presetDanceBtn = document.getElementById('preset-dance');
const presetCharlestonBtn = document.getElementById('preset-charleston');

// Presets Data
const PRESETS = {
    dance: [
        { foot: 'left', note_length: 4, lyric: 'fall', comment: 'L' },
        { foot: 'right', note_length: 4, lyric: 'off', comment: 'R' },
        { foot: 'left', note_length: 4, lyric: 'the', comment: 'L' },
        { foot: 'right', note_length: 4, lyric: 'log', comment: 'R' },
        { foot: 'left', note_length: 4, lyric: 'stomp', comment: 'L' },
        { foot: 'right', note_length: 4, lyric: 'kick', comment: 'R' },
        { foot: 'left', note_length: 4, lyric: 'kickback', comment: 'L' },
        { foot: 'right', note_length: 4, lyric: 'rock', comment: 'R' },
        { foot: 'left', note_length: 4, lyric: 'step', comment: 'L' },
        { foot: 'right', note_length: 4, lyric: 'ball', comment: 'R' },
        { foot: 'left', note_length: 4, lyric: 'tap', comment: 'L' },
        { foot: 'right', note_length: 4, lyric: 'heel', comment: 'R' }
    ],
    charleston: [
        { foot: 'left', note_length: 4, lyric: 'step', comment: 'step forward' },
        { foot: 'right', note_length: 4, lyric: 'kick', comment: 'kick front' },
        { foot: 'right', note_length: 4, lyric: 'step', comment: 'step back' },
        { foot: 'left', note_length: 4, lyric: 'touch', comment: 'touch behind' },
        { foot: 'left', note_length: 4, lyric: 'step', comment: 'step forward' },
        { foot: 'right', note_length: 4, lyric: 'kick', comment: 'kick front' },
        { foot: 'right', note_length: 4, lyric: 'step', comment: 'step back' },
        { foot: 'left', note_length: 4, lyric: 'touch', comment: 'touch behind' }
    ]
};

// Event List Array (Initial State)
let events = [
    { foot: 'left', note_length: 4, lyric: 'kick', comment: 'charleston' },
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

    presetDanceBtn.addEventListener('click', () => loadPreset('dance'));
    presetCharlestonBtn.addEventListener('click', () => loadPreset('charleston'));

    // Wire raw JSON view toggles
    tabTable.addEventListener('click', () => switchEditorView('table'));
    tabJson.addEventListener('click', () => switchEditorView('json'));
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
    }
}

// Load a preset sequence
function loadPreset(key) {
    if (PRESETS[key]) {
        events = JSON.parse(JSON.stringify(PRESETS[key])); // deep copy
        renderTable();
        if (currentView === 'json') {
            rawJsonEditor.value = JSON.stringify(events, null, 4);
            jsonValidationError.classList.add('hidden');
        }
        showView('welcome');
    }
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
            
            // Reload audio tag to play fresh file
            audioPlayer.src = result.files.audio;
            audioPlayer.load();

            // Set download hrefs
            downloadPdf.href = result.files.pdf;
            downloadWav.href = result.files.audio;
            downloadSf2.href = result.files.soundfont;
            downloadMidiVocal.href = result.files.midi_vocal;
            downloadMidiRaw.href = result.files.midi_raw;

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

// Raw JSON View Switching and Validation
function switchEditorView(view) {
    if (view === currentView) return;

    if (view === 'json') {
        // Sync table events to JSON editor
        rawJsonEditor.value = JSON.stringify(events, null, 4);
        jsonValidationError.classList.add('hidden');
        
        tableViewContainer.classList.add('hidden');
        jsonEditorContainer.classList.remove('hidden');
        
        // Hide add/clear buttons since we are in raw text mode
        addRowBtn.classList.add('hidden');
        clearTableBtn.classList.add('hidden');
        
        tabTable.classList.remove('active');
        tabJson.classList.add('active');
        currentView = 'json';
    } else {
        // Switch back to table view: Parse JSON first
        if (syncJsonToTable()) {
            jsonEditorContainer.classList.add('hidden');
            tableViewContainer.classList.remove('hidden');
            
            addRowBtn.classList.remove('hidden');
            clearTableBtn.classList.remove('hidden');
            
            tabJson.classList.remove('active');
            tabTable.classList.add('active');
            currentView = 'table';
        }
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
