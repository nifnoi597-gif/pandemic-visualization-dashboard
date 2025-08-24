<template>
  <div class="data-panel">
    <div v-if="isLoading" class="loading">数据加载中...</div>
    <template v-else>
      <!-- 概要数据卡片 -->
      <div class="summary-cards">
        <div class="card confirmed">
          <h3>总确诊</h3>
          <p class="number">{{ totalConfirmed.toLocaleString() }}</p>
        </div>
        <div class="card deaths">
          <h3>总死亡</h3>
          <p class="number">{{ totalDeaths.toLocaleString() }}</p>
        </div>
        <div class="card recovered">
          <h3>总治愈</h3>
          <p class="number">{{ totalRecovered.toLocaleString() }}</p>
        </div>
      </div>

      <!-- 柱状图容器 -->
      <div class="chart-container">
        <h3>城市确诊排名</h3>
        <div ref="barChartRef" class="chart"></div>
      </div>

      <!-- 折线图容器 -->
      <div class="chart-container" v-if="showTrendChart">
        <h3>疫情趋势</h3>
        <div ref="lineChartRef" class="chart"></div>
      </div>
    </template>
  </div>
</template>

<script setup>
import * as echarts from 'echarts';
import { ref, onMounted, computed, inject, watch } from 'vue';


// 从父组件获取数据
const mockPandemicData = inject('pandemicData');
const currentTimeIndex = inject('currentTimeIndex', ref(0));
const isLoading = inject('isLoading', ref(false)); // 添加加载状态

// 获取图表容器的DOM引用
const barChartRef = ref(null);
const lineChartRef = ref(null);

// 计算总数据（基于当前时间点）
const totalConfirmed = computed(() => {
  if (isLoading.value || !mockPandemicData.value.length) return 0;
  return mockPandemicData.value.reduce((sum, city) => sum + city.timeline[currentTimeIndex.value].confirmed, 0);
});
const totalDeaths = computed(() => {
  if (isLoading.value || !mockPandemicData.value.length) return 0;
  return mockPandemicData.value.reduce((sum, city) => sum + city.timeline[currentTimeIndex.value].deaths, 0);
});
const totalRecovered = computed(() => {
  if (isLoading.value || !mockPandemicData.value.length) return 0;
  return mockPandemicData.value.reduce((sum, city) => sum + city.timeline[currentTimeIndex.value].recovered, 0);
});

// 按确诊数排序的数据（基于当前时间点）
const sortedData = computed(() => {
  if (isLoading.value || !mockPandemicData.value.length) return [];
  return [...mockPandemicData.value]
    .map(city => ({
      name: city.name,
      confirmed: city.timeline[currentTimeIndex.value].confirmed,
      date: city.timeline[currentTimeIndex.value].date
    }))
    .sort((a, b) => b.confirmed - a.confirmed);
});

// 初始化柱状图
const initBarChart = () => {
  if (!barChartRef.value || isLoading.value || !sortedData.value.length) return;
  
  const chart = echarts.init(barChartRef.value);
  
  // 准备柱状图数据
  const cityNames = sortedData.value.map(item => item.name);
  const confirmedData = sortedData.value.map(item => item.confirmed);
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      formatter: function(params) {
        const data = params[0];
        return `${data.name}<br/>确诊: ${data.value} 例`;
      }
    },
   grid: {
  left: '80px', // 增加左边距，给城市名称留更多空间
  right: '4%',
  bottom: '3%',
  containLabel: false // 改为false，手动控制间距
},
    xAxis: {
      type: 'value',
      axisLabel: {
        formatter: '{value} 例'
      }
    },
    yAxis: {
  type: 'category',
  data: cityNames,
  axisLabel: {
    fontSize: 10,
    color: '#8ac6ff',
    // 添加以下配置解决名称显示不全
    interval: 0, // 强制显示所有标签
    width: 60,   // 设置最大宽度
    overflow: 'truncate' // 超出的部分显示省略号
  },
   // 增加左边距给长名称留空间
  axisLine: {
    lineStyle: {
      color: 'rgba(0, 212, 255, 0.5)'
    }
  }
},
    series: [{
      name: '确诊人数',
      type: 'bar',
      data: confirmedData,
      itemStyle: {
      color: function(params) {
        // 根据新的数值大小返回不同颜色
        if (params.value > 2000) return '#ff4d4f'; // 红色
        if (params.value > 500) return '#fa8c16';  // 橙色
        return '#52c41a';                          // 绿色
        }
      },
      label: {
        show: true,
        position: 'right',
        formatter: '{c} 例',
        fontSize: 10
      }
    }]


  };
  
  chart.setOption(option);
  
  window.addEventListener('resize', () => {
    chart.resize();
  });
};

// 初始化折线图
const initLineChart = () => {
  if (!lineChartRef.value || isLoading.value || !mockPandemicData.value.length) return;
  
  // 使用真实数据
  const dates = mockPandemicData.value[0].timeline.map(t => t.date.slice(5));
  const confirmedData = [];
  
  for (let i = 0; i < dates.length; i++) {
    const total = mockPandemicData.value.reduce((sum, city) => sum + city.timeline[i].confirmed, 0);
    confirmedData.push(total);
  }
  
  const chart = echarts.init(lineChartRef.value);
  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: function(params) {
        return `日期: ${params[0].name}<br/>全国确诊: ${params[0].value} 例`;
      }
    },
    xAxis: {
      type: 'category',
      data: dates
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: '{value} 例'
      }
    },
    series: [{
      name: '全国确诊趋势',
      type: 'line',
      data: confirmedData,
      smooth: true,
      lineStyle: {
        color: '#ff4d4f',
        width: 3
      },
      itemStyle: {
        color: '#ff4d4f'
      },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(255, 77, 79, 0.6)' },
          { offset: 1, color: 'rgba(255, 77, 79, 0.1)' }
        ])
      }
    }]
  };
  
  chart.setOption(option);
  window.addEventListener('resize', () => {
    chart.resize();
  });
};

// 监听时间变化和数据加载状态
watch([currentTimeIndex, isLoading], ([newIndex, loading]) => {
  if (!loading) {
    setTimeout(() => {
      initBarChart();
      if (showTrendChart.value) {
        initLineChart();
      }
    }, 100);
  }
});

onMounted(() => {
  // 监听数据加载完成
  if (!isLoading.value) {
    setTimeout(() => {
      initBarChart();
      if (showTrendChart.value) {
        initLineChart();
      }
    }, 100);
  }
});

// 控制是否显示趋势图
const showTrendChart = ref(true);
</script>

<style scoped>
.data-panel {
  height: 100%;
  display: block;
  overflow-y: auto;
  color: #e8f4ff;
}

.loading {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  font-size: 16px;
  color: #00d4ff;
  text-shadow: 0 0 5px rgba(0, 212, 255, 0.5);
}

.summary-cards {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-bottom: 25px;
}

.card {
  padding: 20px;
  border-radius: 8px;
  background: linear-gradient(135deg, rgba(0, 21, 41, 0.8) 0%, rgba(0, 40, 77, 0.8) 100%);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(0, 212, 255, 0.3);
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
}

.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 212, 255, 0.2);
  border-color: rgba(0, 212, 255, 0.5);
}

.card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, #00d4ff, transparent);
}

.card h3 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #8ac6ff;
  font-weight: 500;
  letter-spacing: 1px;
}

.card .number {
  margin: 0;
  font-size: 28px;
  font-weight: bold;
  text-shadow: 0 0 10px currentColor;
}

.card.confirmed .number { 
  color: #ff6b6b; 
  text-shadow: 0 0 10px rgba(255, 107, 107, 0.5);
}
.card.deaths .number { 
  color: #a0a0a0;
  text-shadow: 0 0 10px rgba(160, 160, 160, 0.5);
}
.card.recovered .number { 
  color: #51cf66;
  text-shadow: 0 0 10px rgba(81, 207, 102, 0.5);
}

.chart-container {
  background: linear-gradient(135deg, rgba(0, 21, 41, 0.8) 0%, rgba(0, 40, 77, 0.8) 100%);
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(0, 212, 255, 0.3);
  height: 280px;
  min-height: 280px;
  position: relative;
}

.chart-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(0, 212, 255, 0.3), transparent);
}

.chart-container h3 {
  margin: 0 0 18px 0;
  font-size: 16px;
  color: #00d4ff;
  font-weight: 600;
  text-align: center;
  letter-spacing: 1px;
  text-shadow: 0 0 5px rgba(0, 212, 255, 0.5);
}

.chart {
  height: 220px;
  width: 100%;
  border-radius: 4px;
}

.chart-container:last-child {
  margin-bottom: 0;
}

/* 滚动条样式 */
.data-panel::-webkit-scrollbar {
  width: 6px;
}

.data-panel::-webkit-scrollbar-track {
  background: rgba(0, 21, 41, 0.5);
  border-radius: 3px;
}

.data-panel::-webkit-scrollbar-thumb {
  background: rgba(0, 212, 255, 0.3);
  border-radius: 3px;
}

.data-panel::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 212, 255, 0.5);
}
</style>