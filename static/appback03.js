let selectedFile = null;
let pdfPages = [];
let currentPageIndex = 0;
const BATCH_SIZE = 2; // 每批處理頁數

const fileInput = document.getElementById('fileInput');
const dropZone = document.getElementById('dropZone');
const preview = document.getElementById('preview');
const previewImage = document.getElementById('previewImage');
const clearBtn = document.getElementById('clearBtn');
const processBtn = document.getElementById('processBtn');
const btnText = document.getElementById('btnText');
const loading = document.getElementById('loading');
const errorDiv = document.getElementById('error');
const resultDiv = document.getElementById('result');
const successDiv = document.getElementById('success');
const copyBtn = document.getElementById('copyBtn');
const downloadBtn = document.getElementById('downloadBtn');
const continueBtn = document.getElementById('continueBtn');
const stopBtn = document.getElementById('stopBtn');
const ocrModeSelect = document.getElementById('ocrMode');

let stopProcessing = false;

// 重置狀態
function resetState() {
    selectedFile = null;
    pdfPages = [];
    currentPageIndex = 0;
    stopProcessing = false;
    preview.classList.add('hidden');
    processBtn.disabled = true;
    btnText.innerText = '请先上传图片';
    loading.classList.add('hidden');
    errorDiv.classList.add('hidden');
    resultDiv.innerHTML = '<p class="text-gray-400 text-center mt-20">识别结果将显示在这里</p>';
    successDiv.classList.add('hidden');
    copyBtn.classList.add('hidden');
    downloadBtn.classList.add('hidden');
    continueBtn.classList.add('hidden');
    stopBtn.classList.add('hidden');
}

// 檔案事件
dropZone.addEventListener('click', () => fileInput.click());
dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('dragover'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    handleFiles(e.dataTransfer.files);
});
fileInput.addEventListener('change', (e) => handleFiles(e.target.files));
clearBtn.addEventListener('click', resetState);

function handleFiles(files) {
    if (!files || files.length === 0) return;
    const file = files[0];
    if (!['image/png','image/jpeg','image/jpg','application/pdf'].includes(file.type)) {
        alert('只支持 JPG, PNG 或 PDF');
        return;
    }
    selectedFile = file;
    processBtn.disabled = false;
    btnText.innerText = '开始识别';

    if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = (e) => {
            previewImage.src = e.target.result;
            preview.classList.remove('hidden');
        };
        reader.readAsDataURL(file);
    } else {
        preview.classList.add('hidden');
    }
}

// OCR 主按鈕
processBtn.addEventListener('click', () => {
    if (!selectedFile) return;
    processBtn.disabled = true;
    btnText.innerText = '处理中...';
    loading.classList.remove('hidden');
    errorDiv.classList.add('hidden');
    resultDiv.innerHTML = '';
    successDiv.classList.add('hidden');
    copyBtn.classList.add('hidden');
    downloadBtn.classList.add('hidden');
    continueBtn.classList.add('hidden');
    stopBtn.classList.add('hidden');
    stopProcessing = false;

    if (selectedFile.type === 'application/pdf') {
        handlePDF(selectedFile);
    } else {
        handleImage(selectedFile);
    }
});

function handleImage(file) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('mode', ocrModeSelect.value);

    fetch('/api/ocr', { method:'POST', body: formData })
        .then(res => res.json())
        .then(data => {
            loading.classList.add('hidden');
            if (data.success) {
                resultDiv.innerText = data.text;
                successDiv.classList.remove('hidden');
                copyBtn.classList.remove('hidden');
                downloadBtn.classList.remove('hidden');
            } else {
                errorDiv.innerText = data.error || '未知错误';
                errorDiv.classList.remove('hidden');
            }
            processBtn.disabled = false;
            btnText.innerText = '开始识别';
        })
        .catch(err => {
            loading.classList.add('hidden');
            errorDiv.innerText = err.message;
            errorDiv.classList.remove('hidden');
            processBtn.disabled = false;
            btnText.innerText = '开始识别';
        });
}

function handlePDF(file) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('mode', ocrModeSelect.value);

    fetch('/api/ocr', { method:'POST', body: formData })
        .then(res => res.json())
        .then(data => {
            if (!data.success) {
                loading.classList.add('hidden');
                errorDiv.innerText = data.error || 'PDF OCR 失败';
                errorDiv.classList.remove('hidden');
                processBtn.disabled = false;
                btnText.innerText = '开始识别';
                return;
            }
            pdfPages = data.text.split('=== Page Break ===');
            currentPageIndex = 0;
            displayBatch();
        })
        .catch(err => {
            loading.classList.add('hidden');
            errorDiv.innerText = err.message;
            errorDiv.classList.remove('hidden');
            processBtn.disabled = false;
            btnText.innerText = '开始识别';
        });
}

function displayBatch() {
    if (stopProcessing) return;

    if (currentPageIndex >= pdfPages.length) {
        finishAll();
        return;
    }

    const batch = pdfPages.slice(currentPageIndex, currentPageIndex + BATCH_SIZE);
    resultDiv.innerHTML += batch.join('\n\n') + '\n\n';
    currentPageIndex += BATCH_SIZE;

    loading.classList.add('hidden');

    if (currentPageIndex < pdfPages.length) {
        continueBtn.classList.remove('hidden');
        stopBtn.classList.remove('hidden');
    } else {
        finishAll();
    }
}

function processNextBatch() {
    continueBtn.classList.add('hidden');
    stopBtn.classList.add('hidden');
    loading.classList.remove('hidden');
    setTimeout(displayBatch, 300);
}

function finishAll() {
    loading.classList.add('hidden');
    successDiv.classList.remove('hidden');
    continueBtn.classList.add('hidden');
    stopBtn.classList.add('hidden');
    copyBtn.classList.remove('hidden');
    downloadBtn.classList.remove('hidden');
}

stopBtn.addEventListener('click', () => {
    stopProcessing = true;
    continueBtn.classList.add('hidden');
    stopBtn.classList.add('hidden');
    loading.classList.add('hidden');
    resultDiv.innerHTML += `<p class="text-red-500 text-center">處理已停止</p>`;
});

// 複製 / 下載
copyBtn.addEventListener('click', () => {
    navigator.clipboard.writeText(resultDiv.innerText)
        .then(() => alert('已複製到剪貼簿'));
});
downloadBtn.addEventListener('click', () => {
    const blob = new Blob([resultDiv.innerText], {type:'text/plain;charset=utf-8'});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'ocr_result.txt';
    a.click();
});






