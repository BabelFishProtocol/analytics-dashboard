$(document).ready(function(){

// XUSD Composition
let composition_balances = loaded_balances_data[loaded_balances_data.length-1]['balance'];
total_balance = Object.values(composition_balances).reduce((accumulator, currentValue) => accumulator + currentValue);
// XUSD Composition in dynamics
let composition_dynamics = loaded_balances_data;
// XUSD Flow Data
let sc_net_deposits = loaded_net_deposits_data;
// XUSD Unique Wallets Data
let unique_wallets = loaded_unique_wallets_data;
// XUSD Daily Active Users Data
let daw_json_data = loaded_active_wallets_data;


let tf_data = {};

// constants
const time_type = 'timeseries';
const time_settings = {
    unit: 'day',
    displayFormats: {
        day: 'yyyy-MM-dd'
    },
};

// if the percentage of data value is less than this percentage of the entire dataset, 
// then this data will not be displayed in tooltips and legend
const DATA_CUT_PERCENT = 0.5;


const CHART_COLORS = {
    blue_green: 'rgb(26, 188, 156)',
    green: 'rgb(46, 204, 113)',
    blue: 'rgb(52, 152, 219)',
    purple: 'rgb(155, 89, 182)',
    yellow: 'rgb(241, 196, 15)',
    orange: 'rgb(230, 126, 34)',
    red: 'rgb(231, 76, 60)',
    white_clouds: 'rgb(236, 240, 241)',
    grey: 'rgb(149, 165, 166)'
};


const sc_colors_by_species = {
    'USDT': CHART_COLORS.green,
    'USDC': CHART_COLORS.blue,
    'DAI': CHART_COLORS.orange,
    'BUSD': CHART_COLORS.yellow,
}


// extracting all unique tickers from balances timeseries to assign them specific colors for all charts
var all_unique_tickers = [];
for (let i = 0; i < composition_dynamics.length; i++) {
    let data = composition_dynamics[i].balance;
    Object.keys(data).forEach(ticker =>  {
        if (!is_in_array(ticker, all_unique_tickers)){
            all_unique_tickers.push(ticker);
        }
    });
}

// colors by stablecoin (ticker)
let sc_colors = {}

// assign colors of stablecoins species to all subspecies 
all_unique_tickers.forEach(ticker => {
    Object.keys(sc_colors_by_species).forEach(main_ticker => {
        if (ticker.includes(main_ticker)) {
            sc_colors[ticker] = sc_colors_by_species[main_ticker]; 
        }
    });
});


// general chart colors
if (all_unique_tickers.length > Object.keys(sc_colors).length) {
    let temp_CHART_COLORS = Object.values(CHART_COLORS);
    
    Object.values(sc_colors_by_species).forEach(color => {
        temp_CHART_COLORS = temp_CHART_COLORS.filter(chart_color => chart_color !== color);
    });
    
    all_unique_tickers.forEach(key => {
        console.log(key, ' is not in sc_colors: ', !(key in sc_colors))
        if (!(key in sc_colors)) {
            let random_color = temp_CHART_COLORS[Math.floor(Math.random()*temp_CHART_COLORS.length)];
            sc_colors[key] = random_color;
        }
    });
}


Chart.defaults.color = "#FFFFFF";
Chart.defaults.plugins.tooltip.callbacks.title = sc_flow_tooltip_title;


// general plugins
const getOrCreateLegendList = (chart, id) => {
    const legendContainer = document.getElementById(id);
    let listContainer = legendContainer.querySelector('ul');

    if (!listContainer) {
        listContainer = document.createElement('ul');
        listContainer.style.display = 'flex';
        listContainer.style.flexDirection = 'row';
        listContainer.style.margin = 0;
        listContainer.style.padding = 0;

        legendContainer.appendChild(listContainer);
    }

    return listContainer;
};

const htmlLegendPlugin = {
    id: 'htmlLegend',
    afterUpdate(chart, args, options) {
        const ul = getOrCreateLegendList(chart, options.containerID);

        // Remove old legend items
        while (ul.firstChild) {
            ul.firstChild.remove();
        }

        // Reuse the built-in legendItems generator
        const items = chart.options.plugins.legend.labels.generateLabels(chart);

        items.forEach(item => {
            var dataset_index = 0;
            const dataset_data = chart.data.datasets[dataset_index].data;
            const item_raw_value = dataset_data[item.index];
            const item_value = item_raw_value.toLocaleString('en-US', { style: 'currency', currency: 'USD' });
            const p = ((item_raw_value/total_balance) * 100).toFixed(1);

            if (Math.abs(p) < DATA_CUT_PERCENT) 
                return null

              const li = document.createElement('li');
              li.style.alignItems = 'center';
              li.style.cursor = 'pointer';
              li.style.display = 'flex';
              li.style.flexDirection = 'row';
              li.style.marginLeft = '10px';
              li.style.marginTop = '10px';

              li.onclick = () => {
                const {type} = chart.config;
                if (type === 'pie' || type === 'doughnut') {
                  // Pie and doughnut charts only have a single dataset and visibility is per item
                  chart.toggleDataVisibility(item.index);
                } else {
                  chart.setDatasetVisibility(item.datasetIndex, !chart.isDatasetVisible(item.datasetIndex));
                }
                chart.update();
              };

              // Color box
              const boxSpan = document.createElement('span');
              boxSpan.style.background = item.fillStyle;
              boxSpan.style.borderColor = item.strokeStyle;
              boxSpan.style.borderWidth = item.lineWidth + 'px';
              boxSpan.style.display = 'inline-block';
              boxSpan.style.height = '20px';
              boxSpan.style.marginRight = '10px';
              boxSpan.style.minWidth = '20px';

              // Text
              const textContainer = document.createElement('p');
              textContainer.style.color = item.fontColor;
              textContainer.style.margin = 0;
              textContainer.style.padding = 0;
              textContainer.style.textDecoration = item.hidden ? 'line-through' : '';
              textContainer.style.fontSize = '12px';

              
              let ticker = document.createTextNode(item.text);
              textContainer.appendChild(ticker);
              let linebreak = document.createElement('br');
              textContainer.appendChild(linebreak);
              let value = document.createTextNode(item_value + " (" + p + "%)");
              textContainer.appendChild(value);

              li.appendChild(boxSpan);
              li.appendChild(textContainer);
              ul.appendChild(li);
        });
    }
};


// Vertical annotation line drawing 
var x_pos = 0;
var y_pos = 0;


function getCursorPos(e) {
    let canvas = e.target;
    let cRect = canvas.getBoundingClientRect();
    x_pos = Math.round(e.clientX - cRect.left);
    y_pos = Math.round(e.clientY - cRect.top);
}


const tooltipLine = {
    id: 'tooltipLine',
    afterDraw: chart => {

        if (chart.tooltip._active && chart.tooltip._active.length) {
        const ctx = chart.ctx;
        ctx.save();
        var activePoint = chart.tooltip._active[0];
        
         // draw line
        ctx.beginPath();
        ctx.moveTo(x_pos, chart.chartArea.top);
        ctx.lineTo(x_pos, chart.chartArea.bottom);
        ctx.lineWidth = 1;
        ctx.strokeStyle = '#7f8c8d';
        ctx.stroke();
        ctx.restore();
        }
    }
}


let composition_chart = draw_composition_chart();
let composition_dynamics_chart = draw_composition_dynamics_chart();
let net_deposits_chart = draw_net_deposits_chart();
let net_deposits_collateral_chart = draw_net_deposits_collateral_chart();
let unique_wallets_chart = draw_unique_wallets_chart();
let daw_chart = draw_daw_chart();


composition_dynamics_chart.canvas.addEventListener("mousemove", getCursorPos);
net_deposits_chart.canvas.addEventListener("mousemove", getCursorPos);
net_deposits_collateral_chart.canvas.addEventListener("mousemove", getCursorPos);
unique_wallets_chart.canvas.addEventListener("mousemove", getCursorPos);
daw_chart.canvas.addEventListener("mousemove", getCursorPos);

switch_timeframe('30D');


$('.timeframe__btn').click(function(){
    let timeframe = $(this).data('timeframe');
    switch_timeframe(timeframe);
});


function switch_timeframe(timeframe){
    composition_dynamics_chart.data = tf_data['composition_dynamics'][timeframe];
    composition_dynamics_chart.update();
    net_deposits_chart.data = tf_data['net_deposits'][timeframe];
    net_deposits_chart.update();
    net_deposits_collateral_chart.data = tf_data['net_deposits_collateral'][timeframe];
    net_deposits_collateral_chart.update();
    unique_wallets_chart.data = tf_data['unique_wallets'][timeframe];
    unique_wallets_chart.update();
    daw_chart.data = tf_data['active_wallets'][timeframe];
    daw_chart.update();
}

// XUSD Composition 
function draw_composition_chart(){
    var composition_colors = get_dataset_colors_by_tickers(Object.keys(composition_balances));

    let composition_data = {
        labels: Object.keys(composition_balances),
        datasets: [{
            label: 'XUSD Composition',
            data: Object.values(composition_balances),
            backgroundColor: composition_colors,
            hoverOffset: 15,
            borderWidth: 1,
            borderColor: CHART_COLORS.white_clouds,
        }]
    };
    let composition_config = {
        type: 'pie',
        data: composition_data,
        plugins: [ChartDataLabels, htmlLegendPlugin],
        options: {
            plugins: {
                htmlLegend: {
                    containerID: 'sc-composition__legend-container',
                },
                legend: {
                    display: false,
                    position: 'right',
                    labels: {
                        color: '#FFFFFF',
                    }
                },
                datalabels: {
                    color: '#000000',
                    display: 'auto',
                    clip: true,
                    formatter: function(value, context) {
                        let p = ((value/total_balance) * 100).toFixed(1);
                        if (p < 5)
                            return null;
                        else if (p < 10)
                            return p + '%';
                        return p + '%' + ' ' + context.chart.data.labels[context.dataIndex];
                    },
                    font: {
                        weight: 400,
                        size: 12,
                    },
                },
                tooltip: {
                    callbacks: {
                        label: function(tooltipItem) {
                                let label = tooltipItem.label;
                                let raw_value = tooltipItem.raw;
                                let value = (raw_value).toLocaleString('en-US', { style: 'currency', currency: 'USD' });
                                let p = ((raw_value/total_balance) * 100).toFixed(1);
                                let result = [" " + label, " " + value + " (" + p + "%)"]
                                return result;
                            },
                    },
                    borderWidth: 0
                },
            },
            layout: {
                padding: 15
            },

        },
    };
    let sc_composition_chart = new Chart(
        document.getElementById('sc-composition__canvas'),
        composition_config
    );
    return sc_composition_chart;
}


// XUSD Composition in dynamics
function draw_composition_dynamics_chart(){
    let cd_data = composition_dynamics;
    let cd_labels = convert_timestamps_to_iso_strings(composition_dynamics);

    let datasets_cd = [];
    var datasets_cd_labels = [];
    for (let i = 0; i < cd_data.length; i++){
        datasets_cd_labels.push(...Object.keys(cd_data[i]['balance']));
    }
    datasets_cd_labels = [...new Set(datasets_cd_labels)];
    for (var j = 0; j < datasets_cd_labels.length; j++) {
        let sc_label = datasets_cd_labels[j];
        let dataset = {
            label: sc_label,
            data: cd_data.map(o => o['balance'][sc_label]),
            backgroundColor: sc_colors[sc_label]
        };
        datasets_cd.push(dataset);
    }


    const composition_dynamics_data = {
        labels: cd_labels,
        datasets: datasets_cd
    };

    // console.log(composition_dynamics_data);
    create_tf_data('composition_dynamics', composition_dynamics_data);

    const composition_dynamics_config = {
        type: 'bar',
        data: composition_dynamics_data,
        options: {
            responsive: true,
            interaction: {
              intersect: false,
              axis: 'x'
            },
            plugins: {
                legend: {
                    display: true,                  
                },
                tooltip: {
                    callbacks: {
                        label: sc_flow_tooltip_labels
                    }
                }
            },
            scales: {
                x: {
                    stacked: true,
                    // type: time_type,
                    // time: time_settings
                },
                y: {
                    stacked: true,
                    min: 0,
                }
            }
        },
        plugins: [tooltipLine]
    };

    let sc_composition_dynamics_chart = new Chart(
        document.getElementById('sc-composition-dynamics__canvas'),
        composition_dynamics_config
    );
    return sc_composition_dynamics_chart;
}



// XUSD Flow - Net Deposits
function draw_net_deposits_chart(){
    let nd_data = [];
    let nd_labels = [];
    let backgroundColors = [];
    for (var i = 0; i < sc_net_deposits.length; i++) {
        let date = convert_timestamp_to_iso_string(sc_net_deposits[i].timestamp);
        nd_labels.push(date);
        let deposits_value = sc_net_deposits[i].net_deposits_value;
        nd_data.push(deposits_value);
        if (deposits_value >= 0)
            backgroundColors.push(CHART_COLORS.green);
        else
            backgroundColors.push(CHART_COLORS.red);
    }

    const net_deposits_data = {
        labels: nd_labels,
        datasets: [{
            label: 'Net Deposits Value',
            data: nd_data,
            fill: false,
            borderColor: 'rgb(52, 152, 219)',
            backgroundColor: backgroundColors,
        }]
    };

    create_tf_data('net_deposits', net_deposits_data);

    const net_deposits_config = {
        type: 'bar',
        data: net_deposits_data,
        options: {
            responsive: true,
            interaction: {
              intersect: false,
              axis: 'x'
            },
            plugins: {
                legend: {
                    display: false,                 
                },
                tooltip: {
                    callbacks: {
                        label: function(tooltipItem) {
                            let label = tooltipItem.dataset.label;
                            let raw_value = tooltipItem.raw;
                            let value = (raw_value).toLocaleString('en-US', { style: 'currency', currency: 'USD' });
                            return ' ' + label + ': ' + value;
                        }
                    }
                }
            },
            scales: {
                x: {
                    // type: time_type,
                    // time: time_settings
                }
            }

        },
        plugins: [tooltipLine]
    };
    let sc_flow_net_deposits_chart = new Chart(
        document.getElementById('sc-net-flow__canvas'),
        net_deposits_config
    );
    return sc_flow_net_deposits_chart;
}


// XUSD Flow - Net Deposits By Collateral
function draw_net_deposits_collateral_chart(){
    let nfbc_data = sc_net_deposits;
    let nfbc_labels = [];
    for (var i = 0; i < sc_net_deposits.length; i++) {
        let date = convert_timestamp_to_iso_string(sc_net_deposits[i].timestamp);
        nfbc_labels.push(date);
    }

    let datasets_nfbc = [];
    var datasets_labels = [];
    for (let i = 0; i < nfbc_data.length; i++){
        datasets_labels.push(...Object.keys(nfbc_data[i]['net_deposits_by_collateral']));
    }
    datasets_labels = [...new Set(datasets_labels)];


    for (var j = 0; j < datasets_labels.length; j++) {
        let sc_label = datasets_labels[j];
        let dataset = {
            label: sc_label,
            data: nfbc_data.map(o => o['net_deposits_by_collateral'][sc_label]),
            backgroundColor: sc_colors[sc_label]
        };
        datasets_nfbc.push(dataset);
    }

    const net_deposits_by_collateral_data = {
        labels: nfbc_labels,
        datasets: datasets_nfbc
    };

    create_tf_data('net_deposits_collateral', net_deposits_by_collateral_data);

    const net_deposits_by_collateral_config = {
        type: 'bar',
        data: net_deposits_by_collateral_data,
        options: {
            responsive: true,
            interaction: {
              intersect: false,
              axis: 'x'
            },
            plugins: {
                legend: {
                    display: true,                  
                },
                tooltip: {
                    callbacks: {
                        label: sc_flow_tooltip_labels
                    }
                }
            },
            scales: {
                x: {
                    stacked: true,
                    // type: time_type,
                    // time: time_settings
                },
                y: {
                    stacked: true
                }
            }
        },
        plugins: [tooltipLine]
    };
    let sc_flow_net_deposits_by_collateral_chart = new Chart(
        document.getElementById('sc-net-flow-by-collateral__canvas'),
        net_deposits_by_collateral_config
    );
    return sc_flow_net_deposits_by_collateral_chart;
}


// XUSD Unique Wallets
function draw_unique_wallets_chart(){
    let uw_labels = [];
    let uw_data = [];

    for (var i = 0; i < unique_wallets.length; i++){
        let timestamp = convert_timestamp_to_iso_string(unique_wallets[i].timestamp);
        uw_labels.push(timestamp);
        uw_data.push(unique_wallets[i].unique_wallets_count);
    }


    const unique_wallets_data = {
        labels: uw_labels,
        datasets: [{
            label: 'Unique Wallets',
            data: uw_data,
            fill: false,
            borderColor: CHART_COLORS.blue,
            backgroundColor: CHART_COLORS.blue,
            tension: 0.1,
        }]
    };

    create_tf_data('unique_wallets', unique_wallets_data);

    let unique_wallets_config = {
        type: 'line',
        data: unique_wallets_data,
        options: {
            responsive: true,
            interaction: {
              intersect: false,
              axis: 'x'
            },
            plugins: {
                legend: {
                    display: false,                 
                },
            },
            elements: {
                point:{
                    radius: 0
                }
            },
            scales: {
                x: {
                    // type: time_type,
                    // time: time_settings,
                },
                y: {
                    suggestedMin: 0,
                }

            }
        },
        plugins: [tooltipLine]
    };
    let unique_wallets_chart = new Chart(
        document.getElementById('sc-unique-wallets__canvas'),
        unique_wallets_config
    );

    return unique_wallets_chart;
}


// XUSD Daily Active Users
function draw_daw_chart(){
    let daw_labels = [];
    let daw_data = [];
    for (var i = 0; i < daw_json_data.length; i++){
        let label = convert_timestamp_to_iso_string(daw_json_data[i].timestamp);
        daw_labels.push(label);
        let data = daw_json_data[i].daily_active_wallets_count;
        daw_data.push(data);
    }

    const active_wallets_data = {
        labels: daw_labels,
        datasets: [{
            label: 'Daily Active Users',
            data: daw_data,
            fill: false,
            borderColor: CHART_COLORS.blue,
            backgroundColor: CHART_COLORS.blue,
            tension: 0.1,
        }]
    };
    create_tf_data('active_wallets', active_wallets_data);
    let active_wallets_config = {
        type: 'line',
        data: active_wallets_data,
        options: {
            responsive: true,
            interaction: {
              intersect: false,
              axis: 'x'
            },
            plugins: {
                legend: {
                    display: false,                 
                },
            },
            elements: {
                point:{
                    radius: 0
                }
            },
            scales: {
                x: {
                    // type: time_type,
                    // time: time_settings,
                },
                y: {
                    suggestedMin: 0
                }
            }
        },
        plugins: [tooltipLine]
    };
    let unique_daw_chart = new Chart(
        document.getElementById('sc-daw__canvas'),
        active_wallets_config
    );

    return unique_daw_chart;
}






function convert_timestamp_to_iso_string(timestamp){
    let date = new Date(timestamp).toISOString();
    return date.substring(0, date.indexOf('T'));
}


function convert_timestamps_to_iso_strings(data){
    converted = [];
    for (var i = 0; i < data.length; i++) {
        let date = convert_timestamp_to_iso_string(data[i].timestamp);
        converted.push(date);
    }
    return converted;
}


function is_in_array(object, arr){
    return arr.some(elem => elem === object);
}


function create_tf_data(data_group, chart_data) {
    max_days = chart_data.labels.length;
    year_tf = Math.min(365, max_days);
    months6_tf = Math.min(182, max_days);
    months3_tf = Math.min(91, max_days);

    // console.log(max_days + 'max_days');
    // console.log(year_tf + 'year_tf');
    // console.log(months6_tf + 'six_months_tf');
    // console.log(months3_tf + 'three_months_tf');


    let months3_data = {
        labels: chart_data.labels.slice(-months3_tf),
        datasets: chart_data.datasets.map(ds => ({...ds})), 
    }
    months3_data.datasets.forEach(ds => {
        ds.data = ds.data.slice(-months3_tf);
        if (Array.isArray(ds.backgroundColor))
            ds.backgroundColor = ds.backgroundColor.slice(-months3_tf);
    });


    let months6_data = {
        labels: chart_data.labels.slice(-months6_tf),
        datasets: chart_data.datasets.map(ds => ({...ds})), 
    }
    months6_data.datasets.forEach(ds => {
        ds.data = ds.data.slice(-months6_tf);
        if (Array.isArray(ds.backgroundColor))
            ds.backgroundColor = ds.backgroundColor.slice(-months6_tf);
    });


    let year_data = {
        labels: chart_data.labels.slice(-year_tf),
        datasets: chart_data.datasets.map(ds => ({...ds})), 
    }
    year_data.datasets.forEach(ds => {
        ds.data = ds.data.slice(-year_tf);
        if (Array.isArray(ds.backgroundColor))
            ds.backgroundColor = ds.backgroundColor.slice(-year_tf);
    });


    let days30_data = {
        labels: chart_data.labels.slice(-30),
        datasets: chart_data.datasets.map(ds => ({...ds})), 
    };
    days30_data.datasets.forEach(ds => {
        ds.data = ds.data.slice(-30);
        if (Array.isArray(ds.backgroundColor))
            ds.backgroundColor = ds.backgroundColor.slice(-30);
    });


    tf_data[data_group] = {
        'All': chart_data,
        '30D': days30_data,
        '3M': months3_data,
        '6M': months6_data,
        '1Y': year_data,
    }
}


function sc_flow_tooltip_labels(tooltipItem) {
    total_value = 0;
    tooltipItem.chart.data.datasets.forEach(ds => {
        if (typeof ds.data[tooltipItem.dataIndex] !== 'undefined') {
            total_value += Math.abs(ds.data[tooltipItem.dataIndex]);
        }
    });
    let label = tooltipItem.dataset.label;
    let raw_value = tooltipItem.raw;
    let value = 0;
    let p = 0;
    
    if (typeof raw_value === 'undefined')
        return null;

    value = (raw_value).toLocaleString('en-US', { style: 'currency', currency: 'USD' });
    p = ((raw_value/total_value) * 100).toFixed(1);
    
    
    if (Math.abs(p) < DATA_CUT_PERCENT)
        return null;
    
    let result = " " + label + ":  " + value + " (" + p + "%)";
    return result;
}


function sc_flow_tooltip_title(tooltipItem) {
    let data_index = tooltipItem[0].dataIndex
    let label = tooltipItem[0].chart.data.labels[data_index]
    return label;
}


function get_dataset_colors_by_tickers(tickers) {
    var colors = []
    for(var i = 0; i < tickers.length; i++) {
        colors.push(sc_colors[tickers[i]]);
    }
    return colors;
}


$('#preloader_mask').fadeOut();

})
