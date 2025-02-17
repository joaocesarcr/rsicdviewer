import { AutoTokenizer } from "https://cdn.jsdelivr.net/npm/@huggingface/transformers";

const MAX_TOKENS = 77;
let tokenizer;

// DOM references
const gotoInput = document.getElementById('gotoInput');
const gotoButton = document.getElementById('gotoButton');
const prevButton = document.getElementById('prevButton');
const nextButton = document.getElementById('nextButton');
const currentIndexSpan = document.getElementById('currentIndex');
const totalImagesSpan = document.getElementById('totalImages');
const previewImage = document.getElementById('previewImage');
const originalCaption = document.getElementById('originalCaption');
const editor = document.getElementById('captionEditor');
const saveButton = document.getElementById('saveButton');
const statusMessage = document.getElementById('statusMessage');
const zoomIn = document.getElementById('zoomIn');
const zoomOut = document.getElementById('zoomOut');
const zoomReset = document.getElementById('zoomReset');

// Variables
let currentId = 1;
let totalImages = 23810; 
let currentScale = 1;
const MIN_SCALE = 0.5;
const MAX_SCALE = 10;
const SCALE_STEP = 0.2;
let isDragging = false;
let startX;
let startY;
let translateX = 0;
let translateY = 0;

// Functions
async function handleGoto() {
    const targetId = parseInt(gotoInput.value);
    if (isNaN(targetId) || targetId < 1 || targetId > totalImages) {
        showStatus(`Please enter a valid image number between 1 and ${totalImages}`, false);
        return;
    }
    await loadImage(targetId);
    gotoInput.value = ''; 
}

function updateImageTransform() {
    previewImage.style.transform = `translate(${translateX}px, ${translateY}px) scale(${currentScale})`;
}

async function loadImage(id) {
    try {
        const response = await fetch(`/api/image?id=${id}`);
        if (!response.ok) {
            throw new Error('Failed to load image');
        }
        const imageData = await response.json();
        previewImage.src = '../imagens/' + imageData.path + '.png';
        originalCaption.textContent = imageData.description;
        editor.value = imageData.new_description || imageData.description;
        updateTokenCount();

        currentId = id;
        currentIndexSpan.textContent = currentId;
        updateNavButtons();

        currentScale = 1;
        translateX = 0;
        translateY = 0;
        updateImageTransform();
        editor.focus();
    } catch (error) {
        showStatus('Failed to load image. Please try again.', false);
        console.error('Error:', error);
    }
}

async function saveAndNext() {
    const newDescription = editor.value.trim();
    if (!newDescription) {
        showStatus('Please enter a description before saving.', false);
        return;
    }
    try {
        const response = await fetch('/api/update-description', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                id: currentId,
                description: newDescription
            })
        });
        if (!response.ok) {
            throw new Error('Failed to save description');
        }
        showStatus('Description saved successfully!', true);
        if (currentId < totalImages) {
            await loadImage(currentId + 1);
        }
    } catch (error) {
        showStatus('Failed to save description. Please try again.', false);
        console.error('Error:', error);
    }
}

function updateNavButtons() {
    prevButton.disabled = currentId === 1;
    nextButton.disabled = currentId >= totalImages;
}

function showStatus(message, isSuccess) {
    statusMessage.textContent = message;
    statusMessage.style.display = 'block';
    statusMessage.className = 'status-message ' + 
        (isSuccess ? 'status-success' : 'status-error');
    setTimeout(() => {
        statusMessage.style.display = 'none';
    }, 3000);
}

async function initializeTokenizer() {
    tokenizer = await AutoTokenizer.from_pretrained('openai/clip-vit-base-patch32');
}

async function countTokens(text) {
    const tokens = await tokenizer.encode(text);
    return tokens.length;
}

async function updateTokenCount() {
    const newDescription = editor.value;
    const tokenCount = await countTokens(newDescription);
    document.getElementById("tokenCounter").textContent = `(${tokenCount}/${MAX_TOKENS})`;
    saveButton.disabled = tokenCount > MAX_TOKENS;
}

// Event Listeners
gotoButton.addEventListener('click', handleGoto);

gotoInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        handleGoto();
    }
});

editor.addEventListener('keydown', async function(e) {
    if (e.ctrlKey && e.key === 'Enter') {
        e.preventDefault();
        await saveAndNext();
    }
});

editor.addEventListener("input", updateTokenCount);

prevButton.addEventListener('click', async () => {
    if (currentId > 1) {
        await loadImage(currentId - 1);
    }
});

nextButton.addEventListener('click', async () => {
    if (currentId < totalImages) {
        await loadImage(currentId + 1);
    }
});

saveButton.addEventListener('click', saveAndNext);

zoomIn.addEventListener('click', () => {
    if (currentScale < MAX_SCALE) {
        currentScale = Math.min(currentScale + SCALE_STEP, MAX_SCALE);
        updateImageTransform();
    }
});

zoomOut.addEventListener('click', () => {
    if (currentScale > MIN_SCALE) {
        currentScale = Math.max(currentScale - SCALE_STEP, MIN_SCALE);
        updateImageTransform();
    }
});

zoomReset.addEventListener('click', () => {
    currentScale = 1;
    translateX = 0;
    translateY = 0;
    updateImageTransform();
});

previewImage.addEventListener('mousedown', (e) => {
    e.preventDefault();
    isDragging = true;
    startX = e.clientX - translateX;
    startY = e.clientY - translateY;
    previewImage.style.cursor = 'grabbing';
});

document.addEventListener('mousemove', (e) => {
    if (isDragging) {
        translateX = e.clientX - startX;
        translateY = e.clientY - startY;
        updateImageTransform();
    }
});

document.addEventListener('mouseup', () => {
    isDragging = false;
    previewImage.style.cursor = 'grab';
});

previewImage.addEventListener('wheel', (e) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? -SCALE_STEP : SCALE_STEP;
    const newScale = currentScale + delta;
    if (newScale >= MIN_SCALE && newScale <= MAX_SCALE) {
        currentScale = newScale;
        updateImageTransform();
    }
});

// Initialize
initializeTokenizer();
loadImage(1);
totalImagesSpan.textContent = totalImages;
