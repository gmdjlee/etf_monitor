document.addEventListener('DOMContentLoaded', () => {
    // UI 요소
    const etfList = document.getElementById('etf-list');
    const etfSearch = document.getElementById('etf-search');
    const welcomeMessage = document.getElementById('welcome-message');
    const etfDetails = document.getElementById('etf-details');
    const holdingsTableBody = document.querySelector('#holdings-table tbody');
    const holdingsCountSelect = document.getElementById('holdings-count');
    const chartContainer = document.getElementById('chart-container');
    const weightChartCanvas = document.getElementById('weight-chart');
    const refreshBtn = document.getElementById('refresh-btn');
    const exportCsvBtn = document.getElementById('export-csv-btn');
    const loadingOverlay = document.getElementById('loading-overlay');
    const loadingText = document.getElementById('loading-text');

    // 상태 변수
    let allEtfs = [];
    let currentEtfData = null;
    let holdingsData = [];
    let weightChart = null;

    // --- 유틸리티 함수 ---
    function formatAmount(amount) {
        // 금액을 억원 단위로 변환하여 표시
        const billion = amount / 100000000;
        if (billion >= 1) {
            return `${billion.toFixed(1)}억원`;
        } else {
            const million = amount / 10000000;
            return `${million.toFixed(0)}백만원`;
        }
    }

    // --- 로딩 및 상태 관리 ---
    function showLoading(text = '처리 중입니다...') {
        loadingText.textContent = text;
        loadingOverlay.style.display = 'flex';
        // 다른 기능 lock
        document.body.style.pointerEvents = 'none';
        loadingOverlay.style.pointerEvents = 'auto';
    }

    function hideLoading() {
        loadingOverlay.style.display = 'none';
        document.body.style.pointerEvents = 'auto';
    }

    // --- 데이터 렌더링 ---
    function renderEtfList(etfs) {
        etfList.innerHTML = '';
        if (etfs.length === 0) {
            etfList.innerHTML = '<li>표시할 ETF가 없습니다.</li>';
            return;
        }
        etfs.forEach(etf => {
            const li = document.createElement('li');
            li.textContent = etf.name;
            li.dataset.ticker = etf.ticker;
            etfList.appendChild(li);
        });
    }

    function renderHoldingsTable() {
        holdingsTableBody.innerHTML = '';
        const count = holdingsCountSelect.value;
        const dataToShow = count === 'all' ? holdingsData : holdingsData.slice(0, parseInt(count));

        if (dataToShow.length === 0) {
            holdingsTableBody.innerHTML = '<tr><td colspan="7">구성 종목 정보가 없습니다.</td></tr>';
            return;
        }

        dataToShow.forEach((item, index) => {
            const row = document.createElement('tr');
            row.dataset.stockTicker = item.stock_ticker;
            row.dataset.stockName = item.stock_name;

            const changeClass = item.change > 0 ? 'change-positive' : item.change < 0 ? 'change-negative' : '';
            const statusClass = `status-${item.status === '신규' ? 'new' : item.status === '제외' ? 'removed' : item.status === '비중 증가' ? 'increase' : item.status === '비중 감소' ? 'decrease' : 'hold'}`;

            row.innerHTML = `
                <td>${index + 1}</td>
                <td>${item.stock_name}</td>
                <td class="text-right">${item.prev_weight.toFixed(2)}</td>
                <td class="text-right">${item.current_weight.toFixed(2)}</td>
                <td class="text-right ${changeClass}">${item.change > 0 ? '+' : ''}${item.change.toFixed(2)}</td>
                <td class="text-right amount-cell">${formatAmount(item.current_amount)}</td>
                <td class="${statusClass}">${item.status}</td>
            `;
            holdingsTableBody.appendChild(row);
        });
    }

    function renderWeightChart(stockName, history) {
        chartContainer.classList.remove('hidden');
        document.getElementById('stock-name-chart').textContent = stockName;
        
        const labels = history.map(item => item.date);
        const weightData = history.map(item => item.weight);
        const amountData = history.map(item => item.amount / 100000000); // 억원 단위

        if (weightChart) {
            weightChart.destroy();
        }

        weightChart = new Chart(weightChartCanvas, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: '비중(%)',
                        data: weightData,
                        borderColor: 'rgba(0, 123, 255, 1)',
                        backgroundColor: 'rgba(0, 123, 255, 0.1)',
                        fill: false,
                        tension: 0.1,
                        yAxisID: 'y1'
                    },
                    {
                        label: '평가금액(억원)',
                        data: amountData,
                        borderColor: 'rgba(40, 167, 69, 1)',
                        backgroundColor: 'rgba(40, 167, 69, 0.1)',
                        fill: false,
                        tension: 0.1,
                        yAxisID: 'y2'
                    }
                ]
            },
            options: {
                responsive: true,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                scales: {
                    x: {
                        title: { display: true, text: '날짜' }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: { display: true, text: '비중(%)' },
                        beginAtZero: true
                    },
                    y2: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: { display: true, text: '평가금액(억원)' },
                        beginAtZero: true,
                        grid: {
                            drawOnChartArea: false
                        }
                    }
                }
            }
        });
    }

    // --- API 호출 ---
    async function initializeApp() {
        showLoading('애플리케이션을 초기화하고 있습니다. 잠시만 기다려주세요...');
        try {
            const response = await fetch('/api/initialize', { method: 'POST' });
            const result = await response.json();
            alert(result.message);
            await fetchEtfList();
        } catch (error) {
            console.error('Initialization error:', error);
            alert('초기화 중 오류가 발생했습니다.');
        } finally {
            hideLoading();
        }
    }

    async function fetchEtfList() {
        try {
            const response = await fetch('/api/etfs');
            if (!response.ok) throw new Error('Network response was not ok');
            allEtfs = await response.json();
            renderEtfList(allEtfs);
        } catch (error) {
            console.error('Error fetching ETF list:', error);
        }
    }

    async function fetchEtfDetails(ticker) {
        showLoading('ETF 상세 정보를 불러오는 중입니다...');
        try {
            const response = await fetch(`/api/etf/${ticker}`);
            if (!response.ok) throw new Error('Network response was not ok');
            
            currentEtfData = await response.json();
            holdingsData = currentEtfData.comparison;
            
            welcomeMessage.classList.add('hidden');
            etfDetails.classList.remove('hidden');
            chartContainer.classList.add('hidden');
            if (weightChart) weightChart.destroy();
            
            const selectedEtf = allEtfs.find(e => e.ticker === ticker);
            document.getElementById('etf-name').textContent = selectedEtf ? selectedEtf.name : 'Unknown ETF';
            document.getElementById('etf-ticker').textContent = `TICKER: ${currentEtfData.etf_ticker}`;
            document.getElementById('etf-dates').textContent = `비교 기간: ${currentEtfData.prev_date} vs ${currentEtfData.current_date}`;
            
            renderHoldingsTable();
        } catch (error) {
            console.error('Error fetching ETF details:', error);
            alert('ETF 상세 정보를 가져오는 데 실패했습니다.');
        } finally {
            hideLoading();
        }
    }

    async function fetchStockHistory(etfTicker, stockTicker, stockName) {
        showLoading('종목 비중 추이를 불러오는 중입니다...');
        try {
            const response = await fetch(`/api/etf/${etfTicker}/stock/${stockTicker}`);
            if (!response.ok) throw new Error('Network response was not ok');
            const history = await response.json();
            renderWeightChart(stockName, history);
        } catch (error) {
            console.error('Error fetching stock history:', error);
            alert('종목 비중 추이를 가져오는 데 실패했습니다.');
        } finally {
            hideLoading();
        }
    }

    // --- 이벤트 리스너 ---
    etfSearch.addEventListener('input', (e) => {
        const searchTerm = e.target.value.toLowerCase();
        const filteredEtfs = allEtfs.filter(etf => 
            etf.name.toLowerCase().includes(searchTerm) || etf.ticker.includes(searchTerm)
        );
        renderEtfList(filteredEtfs);
    });

    etfList.addEventListener('click', (e) => {
        if (e.target.tagName === 'LI' && e.target.dataset.ticker) {
            const ticker = e.target.dataset.ticker;
            
            // 활성 클래스 관리
            const currentActive = etfList.querySelector('.active');
            if (currentActive) {
                currentActive.classList.remove('active');
            }
            e.target.classList.add('active');

            fetchEtfDetails(ticker);
        }
    });

    holdingsCountSelect.addEventListener('change', renderHoldingsTable);

    holdingsTableBody.addEventListener('click', (e) => {
        const row = e.target.closest('tr');
        if (row && row.dataset.stockTicker && currentEtfData) {
            const stockTicker = row.dataset.stockTicker;
            const stockName = row.dataset.stockName;
            fetchStockHistory(currentEtfData.etf_ticker, stockTicker, stockName);
        }
    });

    refreshBtn.addEventListener('click', async () => {
        showLoading('최신 데이터로 업데이트 중입니다...');
        try {
            const response = await fetch('/api/refresh', { method: 'POST' });
            const result = await response.json();
            alert(result.message);
            // 현재 선택된 ETF가 있다면, 해당 정보도 새로고침
            const activeEtf = etfList.querySelector('.active');
            if (activeEtf) {
                await fetchEtfDetails(activeEtf.dataset.ticker);
            }
        } catch (error) {
            console.error('Refresh error:', error);
            alert('데이터 업데이트 중 오류가 발생했습니다.');
        } finally {
            hideLoading();
        }
    });

    exportCsvBtn.addEventListener('click', () => {
        if (currentEtfData) {
            window.location.href = `/api/export/csv/${currentEtfData.etf_ticker}`;
        } else {
            alert('먼저 ETF를 선택해주세요.');
        }
    });


    // --- 앱 시작 ---
    initializeApp();
});