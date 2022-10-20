$(document).ready(function(){

let tf_data = {};

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


// constants
const time_type = 'timeseries';
const time_settings = {
    unit: 'day',
    displayFormats: {
        day: 'yyyy-MM-dd'
    },
};


Chart.defaults.color = "#FFFFFF";
// Chart.defaults.plugins.tooltip.callbacks.title = sc_flow_tooltip_title;


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


var price_chart = draw_price_chart();
var market_cap_chart = draw_market_cap_chart();
// var circ_supply_chart = draw_circ_supply_chart();
var locked_funds_chart = draw_locked_funds_chart();
var unique_wallets_chart = draw_unique_wallets_chart();
var daw_chart = draw_active_wallets_chart();
var emission_chart = draw_emission_schedule_chart();
var distribution_chart = draw_distribution_chart();


switch_timeframe('30D');


$('.timeframe__btn').click(function(){
    let timeframe = $(this).data('timeframe');
    switch_timeframe(timeframe);
});

function switch_timeframe(timeframe){
    price_chart.data = tf_data['prices'][timeframe];
    price_chart.update();
    market_cap_chart.data = tf_data['market_cap'][timeframe];
    market_cap_chart.update();
    // circ_supply_chart.data = tf_data['circulating_supply'][timeframe];
    // circ_supply_chart.update();
    locked_funds_chart.data = tf_data['locked_funds'][timeframe];
    locked_funds_chart.update();
    unique_wallets_chart.data = tf_data['unique_wallets'][timeframe];
    unique_wallets_chart.update();
    daw_chart.data = tf_data['active_wallets'][timeframe];
    daw_chart.update();
}




function draw_price_chart(){
    let data_usd = loaded_price_data.map(o => o.prices.USD);
    let data_btc = loaded_price_data.map(o => o.prices.WRBTC * 100000000);
    let timestamp_labels = loaded_price_data.map(o => convert_timestamp_to_iso_string(o.timestamp));

    const prices_data = {
        labels: timestamp_labels,
        datasets: [
            {
                label: 'USD',
                data: data_usd,
                fill: false,
                borderColor: CHART_COLORS.blue,
                backgroundColor: CHART_COLORS.blue,
                yAxisID: 'y',
            }, 
            {
                label: 'BTC (sats)',
                data: data_btc,
                fill: false,
                borderColor: CHART_COLORS.yellow,
                backgroundColor: CHART_COLORS.yellow,
                yAxisID: 'y1',
                is_not_currency: true,
                nc_rounding_digits: 0
            }]
    };

    create_tf_data('prices', prices_data);

    let stacked=false, double_axis=true;
    return draw_line_chart('price__canvas', prices_data, stacked, double_axis);
}


function draw_market_cap_chart(){
    let data_usd = loaded_market_cap_data.map(o => o.market_cap.USD);
    let data_btc = loaded_market_cap_data.map(o => o.market_cap.WRBTC);
    let timestamp_labels = loaded_market_cap_data.map(o => convert_timestamp_to_iso_string(o.timestamp));

    const mc_data = {
        labels: timestamp_labels,
        datasets: [
            {
                label: 'USD',
                data: data_usd,
                fill: false,
                borderColor: CHART_COLORS.blue,
                backgroundColor: CHART_COLORS.blue,
                yAxisID: 'y',
            }, 
            {
                label: 'BTC',
                data: data_btc,
                fill: false,
                borderColor: CHART_COLORS.yellow,
                backgroundColor: CHART_COLORS.yellow,
                yAxisID: 'y1',
                is_not_currency: true,
                nc_rounding_digits: 2
            }]
    };

    create_tf_data('market_cap', mc_data);

    let stacked=false, double_axis=true;
    return draw_line_chart('market-cap__canvas', mc_data, stacked, double_axis);
}


function draw_circ_supply_chart(){
    let data = loaded_circ_supply.map(o => o.circulating_supply);
    let timestamp_labels = loaded_circ_supply.map(o => convert_timestamp_to_iso_string(o.timestamp));

    const cs_data = {
        labels: timestamp_labels,
        datasets: [{
                label: 'FISH',
                data: data,
                fill: false,
                borderColor: CHART_COLORS.blue,
                backgroundColor: CHART_COLORS.blue,
                yAxisID: 'y',
                is_not_currency: true,
            }]
    };

    create_tf_data('circulating_supply', cs_data);

    let stacked=false, double_axis=false, custom_scales=null, display_legend=false;
    return draw_line_chart('circulating_supply__canvas', cs_data, stacked, double_axis, custom_scales, display_legend);
}


function draw_locked_funds_chart(){
    let vesting_data = loaded_vesting.map(o => o.funds_in_vesting);
    let staking_data = loaded_staking.map(o => o.funds_in_staking);
    let multisig_data = loaded_multisig_balance.map(o => o.balance);
    let circulating_supply = loaded_circ_supply.map(o => o.circulating_supply);

    let released_data = loaded_released_funds.map(o => o.balance);
    let vote_locked_data = loaded_vote_locked_funds.map(o => o.balance);

    let timestamp_labels = loaded_multisig_balance.map(o => convert_timestamp_to_iso_string(o.timestamp));

    const lf_data = {
        labels: timestamp_labels,
        datasets: [
            {
                label: 'Circulating Supply',
                data: circulating_supply,
                // fill: false,
                borderColor: CHART_COLORS.white_clouds,
                backgroundColor: 'rgba(236, 240, 241, 0.7)', //CHART_COLORS.blue,
                is_not_currency: true,
                show_share_of_total: true,
                nc_rounding_digits: 0,
                tension: 0.4,
                fill: 'origin',
            },

            // {
            //     label: 'Vesting',
            //     data: vesting_data,
            //     // fill: false,
            //     borderColor: CHART_COLORS.purple,
            //     backgroundColor: 'rgba(155, 89, 182, 0.7)',
            //     is_not_currency: true,
            //     nc_rounding_digits: 0,
            //     tension: 0.4,
            //     fill: 'origin',

            // }, 
            // {
            //     label: 'Staking',
            //     data: staking_data,
            //     // fill: false,
            //     borderColor: CHART_COLORS.blue_green,
            //     backgroundColor: 'rgba(26, 188, 156, 0.7)',
            //     is_not_currency: true,
            //     nc_rounding_digits: 0,
            //     tension: 0.4,
            //     fill: 'origin',
            // },
            // {
            //     label: 'Multisig',
            //     data: multisig_data,
            //     // fill: false,
            //     borderColor: CHART_COLORS.blue,
            //     backgroundColor: 'rgba(52, 152, 219, 0.7)', //CHART_COLORS.blue,
            //     is_not_currency: true,
            //     nc_rounding_digits: 0,
            //     tension: 0.4,
            //     fill: 'origin',
            // },
            {
                label: 'Vote-Locked Funds',
                data: vote_locked_data,
                // fill: false,
                borderColor: CHART_COLORS.purple,
                backgroundColor: 'rgba(155, 89, 182, 0.7)',
                is_not_currency: true,
                show_share_of_total: true,
                nc_rounding_digits: 0,
                tension: 0.4,
                fill: 'origin',
            },
            {
                label: 'Released Funds',
                data: released_data,
                // fill: false,
                borderColor: CHART_COLORS.blue,
                backgroundColor: 'rgba(52, 152, 219, 0.7)',
                is_not_currency: true,
                show_share_of_total: true,
                nc_rounding_digits: 0,
                tension: 0.4,
                fill: 'origin',
            },
            

            
            ]
    };


    create_tf_data('locked_funds', lf_data);

    let custom_scales = {
                y: {
                    min: 0,
                    max: total_supply,
                }
            };

    let stacked=false, double_axis=false;
    return draw_line_chart('locked-funds__canvas', lf_data, stacked, double_axis, custom_scales);
}


function draw_unique_wallets_chart(){
    let data = loaded_unique_wallets_data.map(o => o.unique_wallets_count);
    let timestamp_labels = loaded_unique_wallets_data.map(o => convert_timestamp_to_iso_string(o.timestamp));

    const uw_data = {
        labels: timestamp_labels,
        datasets: [{
                label: 'Unique Wallets',
                data: data,
                fill: false,
                borderColor: CHART_COLORS.blue,
                backgroundColor: CHART_COLORS.blue,
                is_not_currency: true,
                nc_rounding_digits: 0
            }]
    };


    create_tf_data('unique_wallets', uw_data);

    let custom_scales = {
                y: {
                    suggestedMin: 0,
                }
            };

    let stacked=false, double_axis=false, display_legend=false;
    return draw_line_chart('unique-wallets__canvas', uw_data, stacked, double_axis, custom_scales, display_legend);
}


function draw_active_wallets_chart(){
    let data = loaded_active_wallets_data.map(o => o.daily_active_wallets_count);
    let timestamp_labels = loaded_active_wallets_data.map(o => convert_timestamp_to_iso_string(o.timestamp));

    const daw_data = {
        labels: timestamp_labels,
        datasets: [{
                label: 'Active Users',
                data: data,
                fill: false,
                borderColor: CHART_COLORS.blue,
                backgroundColor: CHART_COLORS.blue,
                is_not_currency: true,
                nc_rounding_digits: 0
            }]
    };

    create_tf_data('active_wallets', daw_data);

    let custom_scales = {
                y: {
                    suggestedMin: 0,
                }
            };

    let stacked=false, double_axis=false, display_legend=false;
    return draw_line_chart('daw__canvas', daw_data, stacked, double_axis, custom_scales, display_legend);
}


function draw_emission_schedule_chart(){
    let vesting_data = loaded_vesting.map(o => o.funds_in_vesting);
    
    let team_fund = [0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  2800000.00,  5600000.00,  8400000.00,  11200000.00, 14000000.00, 16800000.00, 19600000.00, 22400000.00, 25200000.00, 28000000.00, 30800000.00, 33600000.00, 36400000.00, 39200000.00, 42000000.00, 44800000.00, 47600000.00, 50400000.00, 53200000.00, 56000000.00, 58800000.00, 61600000.00, 64400000.00, 67200000.00, 70000000.00, 72800000.00, 75600000.00, 78400000.00, 81200000.00, 84000000.00, 84000000.00, 84000000.00, 84000000.00, 84000000.00, 84000000.00, 84000000.00, 84000000.00, 84000000.00, 84000000.00, 84000000.00, 84000000.00, 84000000.00, 84000000.00, 84000000.00, 84000000.00, 84000000.00, 84000000.00, 84000000.00, 84000000.00, 84000000.00, 84000000.00, 84000000.00, 84000000.00, 84000000.00 ];
    let development_fund = [1470000, 2940000, 4410000, 5880000, 7350000, 8820000, 10290000, 11760000, 13230000, 14700000, 16170000, 17640000, 19110000, 20580000, 22050000, 23520000, 24990000, 26460000, 27930000, 29400000, 30870000, 32340000, 33810000, 35280000, 35560000, 35840000, 36120000, 36400000, 36680000, 36960000, 37240000, 37520000, 37800000, 38080000, 38360000, 38640000, 38920000, 39200000, 39480000, 39760000, 40040000, 40320000, 40600000, 40880000, 41160000, 41440000, 41720000, 42000000, 42000000, 42000000, 42000000, 42000000, 42000000, 42000000, 42000000, 42000000, 42000000, 42000000, 42000000, 42000000];
    let ecosystem_fund = [21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000, 21000000];
    let liquidity_mining = [5950000,  11900000, 17850000, 23800000, 29750000, 35700000, 41650000, 47600000, 53550000, 59500000, 65450000, 71400000, 75600000, 79800000, 84000000, 88200000, 92400000, 96600000, 100800000, 105000000, 109200000, 113400000, 117600000, 121800000, 124250000, 126700000, 129150000, 131600000, 134050000, 136500000, 138950000, 141400000, 143850000, 146300000, 148750000, 151200000, 151900000, 152600000, 153300000, 154000000, 154700000, 155400000, 156100000, 156800000, 157500000, 158200000, 158900000, 159600000, 160300000, 161000000, 161700000, 162400000, 163100000, 163800000, 164500000, 165200000, 165900000, 166600000, 167300000, 168000000 ];
    let token_sale_one = [3250800.00, 6501600.00, 9752400.00, 13003200.00,  16254000.00,  19504800.00,  22755600.00,  26006400.00,  29257200.00,  32508000.00,  32508000.00,  32508000.00,  32508000.00,  32508000.00,  32508000.00,  32508000.00,  32508000.00,  32508000.00,  32508000.00,  32508000.00,  32508000.00,  32508000.00,  32508000.00,  32508000.00,  32508000.00,  32508000.00,  32508000.00,  32508000.00,  32508000.00,  32508000.00,  32508000.00,  32508000.00,  32508000.00,  32508000.00,  32508000.00,  32508000.00,  32508000.00,  32508000.00,  32508000.00,  32508000.00,  32508000.00,  32508000.00,  32508000.00,  32508000.00,  32508000.00,  32508000.00,  32508000.00,  32508000.00,  32508000.00,  32508000.00,  32508000.00,  32508000.00,  32508000.00,  32508000.00,  32508000.00,  32508000.00,  32508000.00,  32508000.00,  32508000.00,  32508000.00, ];
    let token_sale_two = [10995600.00,  11995200.00,  12994800.00,  13994400.00,  14994000.00,  15993600.00,  16993200.00,  17992800.00,  18992400.00,  19992000.00,  19992000.00,  19992000.00,  19992000.00,  19992000.00,  19992000.00,  19992000.00,  19992000.00,  19992000.00,  19992000.00,  19992000.00,  19992000.00,  19992000.00,  19992000.00,  19992000.00,  19992000.00,  19992000.00,  19992000.00,  19992000.00,  19992000.00,  19992000.00,  19992000.00,  19992000.00,  19992000.00,  19992000.00,  19992000.00,  19992000.00,  19992000.00,  19992000.00,  19992000.00,  19992000.00,  19992000.00,  19992000.00,  19992000.00,  19992000.00,  19992000.00,  19992000.00,  19992000.00,  19992000.00,  19992000.00,  19992000.00,  19992000.00,  19992000.00,  19992000.00,  19992000.00,  19992000.00,  19992000.00,  19992000.00,  19992000.00,  19992000.00,  19992000.00, ];
    let sovryn_amm = [10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,  10500000.00,];
    let early_supporters = [0.00, 0.00, 0.00, 0.00, 2100000.00, 4200000.00, 6300000.00, 8400000.00, 10500000.00,  12600000.00,  14700000.00,  16800000.00,  18900000.00,  21000000.00,  23100000.00,  25200000.00,  27300000.00,  29400000.00,  31500000.00,  33600000.00,  35700000.00,  37800000.00,  39900000.00,  42000000.00,  42000000.00,  42000000.00,  42000000.00,  42000000.00,  42000000.00,  42000000.00,  42000000.00,  42000000.00,  42000000.00,  42000000.00,  42000000.00,  42000000.00,  42000000.00,  42000000.00,  42000000.00,  42000000.00,  42000000.00,  42000000.00,  42000000.00,  42000000.00,  42000000.00,  42000000.00,  42000000.00,  42000000.00,  42000000.00,  42000000.00,  42000000.00,  42000000.00,  42000000.00,  42000000.00,  42000000.00,  42000000.00,  42000000.00,  42000000.00,  42000000.00,  42000000.00, ];
    
    let timestamp_labels = ['Month 1', 'Month 2', 'Month 3', 'Month 4', 'Month 5', 'Month 6', 'Month 7', 'Month 8', 'Month 9', 'Month 10', 'Month 11', 'Month 12', 'Month 13', 'Month 14', 'Month 15', 'Month 16', 'Month 17', 'Month 18', 'Month 19', 'Month 20', 'Month 21', 'Month 22', 'Month 23', 'Month 24', 'Month 25', 'Month 26', 'Month 27', 'Month 28', 'Month 29', 'Month 30', 'Month 31', 'Month 32', 'Month 33', 'Month 34', 'Month 35', 'Month 36', 'Month 37', 'Month 38', 'Month 39', 'Month 40', 'Month 41', 'Month 42', 'Month 43', 'Month 44', 'Month 45', 'Month 46', 'Month 47', 'Month 48', 'Month 49', 'Month 50', 'Month 51', 'Month 52', 'Month 53', 'Month 54', 'Month 55', 'Month 56', 'Month 57', 'Month 58', 'Month 59', 'Month 60'];

    const es_data = {
        labels: timestamp_labels,
        datasets: [
            
            {
                label: 'Ecosystem Fund',
                data: ecosystem_fund,
                // fill: false,
                borderColor: 'rgb(155,187,89)',
                backgroundColor: 'rgb(155,187,89)',
                is_not_currency: true,
                show_share_of_total: true,
                nc_rounding_digits: 0,
                tension: 0.4,
                fill: 'origin',
            },
            {
                label: 'Token Sale One',
                data: token_sale_one,
                // fill: false,
                borderColor: 'rgb(75,172,198)',
                backgroundColor: 'rgb(75,172,198)',
                is_not_currency: true,
                show_share_of_total: true,
                nc_rounding_digits: 0,
                tension: 0.4,
                fill: 'origin',
            },
            {
                label: 'Development Fund',
                data: development_fund,
                // fill: false,
                borderColor: 'rgb(192,80,77)',
                backgroundColor: 'rgb(192,80,77)',
                is_not_currency: true,
                show_share_of_total: true,
                nc_rounding_digits: 0,
                tension: 0.4,
                fill: 'origin',
            },
            {
                label: 'Team Fund',
                data: team_fund,
                // fill: false,
                borderColor: 'rgb(79,129,189)',
                backgroundColor: 'rgb(79,129,189)',
                is_not_currency: true,
                show_share_of_total: true,
                nc_rounding_digits: 0,
                tension: 0.4,
                fill: 'origin',
            },
            {
                label: 'Liquidity Mining',
                data: liquidity_mining,
                // fill: false,
                borderColor: 'rgb(128,100,162)',
                backgroundColor: 'rgb(128,100,162)',
                is_not_currency: true,
                show_share_of_total: true,
                nc_rounding_digits: 0,
                tension: 0.4,
                fill: 'origin',
            },
            {
                label: 'Token Sale Two',
                data: token_sale_two,
                // fill: false,
                borderColor: 'rgb(247,150,70)',
                backgroundColor: 'rgb(247,150,70)',
                is_not_currency: true,
                show_share_of_total: true,
                nc_rounding_digits: 0,
                tension: 0.4,
                fill: 'origin',
            },
            {
                label: 'Sovryn AMM',
                data: sovryn_amm,
                // fill: false,
                borderColor: 'rgb(138,172,211)',
                backgroundColor: 'rgb(138,172,211)',
                is_not_currency: true,
                show_share_of_total: true,
                nc_rounding_digits: 0,
                tension: 0.4,
                fill: 'origin',
            },
            {
                label: 'Early Supporters',
                data: early_supporters,
                // fill: false,
                borderColor: 'rgb(225,172,170)',
                backgroundColor: 'rgb(225,172,170)',
                is_not_currency: true,
                show_share_of_total: true,
                nc_rounding_digits: 0,
                tension: 0.4,
                fill: 'origin',
            },

            

            
            // {
            //     label: 'Released Funds',
            //     data: released_data,
            //     // fill: false,
            //     borderColor: CHART_COLORS.blue,
            //     backgroundColor: 'rgba(52, 152, 219, 0.7)',
            //     is_not_currency: true,
            //     nc_rounding_digits: 0,
            //     tension: 0.4,
            //     fill: 'origin',
            // },
            ]
    };


    // create_tf_data('locked_funds', lf_data);

    let custom_scales = {
                y: {
                    min: 0,
                    max: total_supply,
                }
            };

    let stacked=true, double_axis=false;
    return draw_line_chart('emission-schedule__canvas', es_data, stacked, double_axis, custom_scales);
}


function draw_distribution_chart(){
    const data = {
        labels: ['Team', 'Development Fund', 'Ecosystem Fund', 'Liquidity Mining', 'Token Sale One', 'Token Sale Two', 'Sovryn AMM', 
        'Early Supporters'],
        datasets: [
            {
              label: 'Dataset 1',
              data: [20, 10, 5, 40, 7.74, 4.76, 2.5, 10],
              backgroundColor: ['rgb(79,129,189)', 'rgb(192,80,77)', 'rgb(155,187,89)', 'rgb(128,100,162)', 'rgb(75,172,198)', 
              'rgb(247,150,70)', 'rgb(138,172,211)', 'rgb(225,172,170)'],
              hoverOffset: 15,
              borderWidth: 1,
              borderColor: CHART_COLORS.white_clouds,
            }
        ]
    };
    draw_pie_chart('funds-distribution__canvas', data);
}


function draw_line_chart(canvas_id, data, stacked=false, double_axis=false, custom_scales=null, display_legend=true) {
    let scales_config = {}

    if (double_axis) {
        scales_config = {
            y: {
                type: 'linear',
                display: true,
                position: 'left',
            },
            y1: {
                type: 'linear',
                display: true,
                position: 'right',

                // grid line settings
                grid: {
                  drawOnChartArea: false, // only want the grid lines for one axis to show up
                },
            },
        }
    }
    
    if (custom_scales !== null) {
        scales_config = custom_scales;
    }

    if ("y" in scales_config) {
        scales_config.y.stacked = stacked;
    }
    


    const config = {
        type: 'line',
        data: data,
        options: {
            responsive: true,
            interaction: {
                intersect: false,
                mode: 'index'
                // axis: 'x'
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: draw_tooltips
                    }
                },
                legend: {
                    display: display_legend,           
                },

            },
            scales: scales_config,
            elements: {
                point:{
                    radius: 0
                }
            }
        },
        plugins: [tooltipLine]
    };
    let chart = new Chart(
        document.getElementById(canvas_id),
        config
    );
    chart.canvas.addEventListener("mousemove", getCursorPos);
    return chart;
}


function draw_pie_chart(canvas_id, data) {
    const config = {
        type: 'pie',
        data: data,
        plugins: [ChartDataLabels],
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'right',
                },
                datalabels: {
                    color: '#000000',
                    display: 'auto',
                    clip: true,
                    formatter: function(value, context) {
                        let p = (value).toFixed(1);
                        if (p < 5)
                            return null;
                        else if (p < 10)
                            return p + '%';
                        return p + '%';
                    },
                    font: {
                        weight: 400,
                        size: 12,
                    },
                },
            title: {
                    display: false,
                    text: 'Pie Chart'
                }
            },
            layout: {
                padding: 7
            }
                
        },
    };
    let chart = new Chart(
        document.getElementById(canvas_id),
        config
    );
    chart.canvas.addEventListener("mousemove", getCursorPos);
    // chart.canvas.style.width = 400;
    // chart.canvas.style.height = 200;
    return chart;
}


function convert_timestamp_to_iso_string(timestamp){
    let date = new Date(timestamp).toISOString();
    return date.substring(0, date.indexOf('T'));
}


function draw_tooltips(tooltipItem) {
    let dataIndex = tooltipItem.dataIndex;

    // console.log(tooltipItem.dataset.collateral_asset_data[dataIndex] + ' ' + tooltipItem.dataset.collateral_asset_ticker);
    let label = tooltipItem.dataset.label;
    let raw_value = tooltipItem.raw;
    let value = (raw_value).toLocaleString('en-US', { style: 'currency', currency: 'USD' });
    let share = null;

    if ("is_not_currency" in tooltipItem.dataset){
        value = raw_value;

        if ("nc_rounding_digits" in tooltipItem.dataset) {
            value = value.toFixed(tooltipItem.dataset["nc_rounding_digits"]);
        }

        const notCurrencyFractionDigits = new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
        }).resolvedOptions().maximumFractionDigits;

        value = parseFloat(value).toLocaleString('en-US', { maximumFractionDigits: notCurrencyFractionDigits });
    }

    if ("show_share_of_total" in tooltipItem.dataset){
        share = ((raw_value/total_supply) * 100).toFixed(1) + '%';
    }

    if (raw_value == 0) {
        return
    }
    if ("raw_data" in tooltipItem.dataset) {
        let col_asset_ticker = Object.keys(tooltipItem.dataset.raw_data[dataIndex])[0];
        let col_asset_value = Math.floor(tooltipItem.dataset.raw_data[dataIndex][col_asset_ticker]);
        
        return ' ' + label + ': ' + value + ' (' + col_asset_value + ' ' + col_asset_ticker + ')';
    }

    if (typeof share === "string") {
        return ' ' + label + ': ' + value + ' ('+ share +')';
    }

    return ' ' + label + ': ' + value;


}


// function create_tf_data(data_group, chart_data) {
//     let days30_data = {
//        labels: chart_data.labels.slice(-30),
//        datasets: chart_data.datasets.map(ds => ({...ds})), 
//     };
//     days30_data.datasets.forEach(ds => {
//         ds.data = ds.data.slice(-30);
//         if (Array.isArray(ds.backgroundColor))
//             ds.backgroundColor = ds.backgroundColor.slice(-30);
//     });
//     tf_data[data_group] = {
//         'All': chart_data,
//         '30D': days30_data
//     }
// }


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




$('#preloader_mask').fadeOut();


})