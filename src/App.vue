<template>
  <div id="app">
    <h1>疫情数据可视化大屏</h1>
    <div v-if="isLoading" class="loading">数据加载中...</div>
    <div v-else class="dashboard-container">
      <div class="sidebar">
        <DataPanel />
      </div>
      <div class="map-area">
        <MapContainer />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, provide, onMounted } from 'vue';
// 必须导入这两个组件！
import DataPanel from './components/DataPanel.vue';
import MapContainer from './components/MapContainer.vue';

const mockPandemicData = ref([]);
const currentTimeIndex = ref(0);
const isLoading = ref(true);

// 获取API数据
const fetchPandemicData = async () => {
  try {
    const response = await fetch('http://127.0.0.1:8000/api/pandemic-data');
    // 或者使用相对路径，但需要配置代理
    // const response = await fetch('/api/pandemic-data');
    const data = await response.json();
    mockPandemicData.value = data;
    isLoading.value = false;
  } catch (error) {
    console.error('获取数据失败:', error);
    // 这里先添加备用数据确保页面能显示
    isLoading.value = false;
  }
};

onMounted(() => {
  fetchPandemicData();
});

provide('pandemicData', mockPandemicData);
provide('currentTimeIndex', currentTimeIndex);
provide('isLoading', isLoading);
</script>

<style>
/* 深色科技风背景 */
#app {
  margin: 0 !important;
  padding: 0 !important;
  width: 100vw !important;
  height: 100vh !important;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, #0c0e2a 0%, #1a1f4b 50%, #0c0e2a 100%);
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

/* 科技感标题 - 已优化 */
h1 {
  margin: 0 !important;
  padding: 18px 20px;
  background: linear-gradient(135deg, #001529 0%, #003366 100%);
  color: #00d4ff !important;
  box-shadow: 0 0 20px rgba(0, 212, 255, 0.4);
  z-index: 1000;
  flex-shrink: 0;
  font-size: 22px;
  font-weight: 600;
  text-align: center;
  letter-spacing: 3px;
  text-transform: uppercase;
  border-bottom: 2px solid rgba(0, 212, 255, 0.3);
  text-shadow: 0 0 10px rgba(0, 212, 255, 0.7);
  position: relative;
  overflow: hidden;
}

/* 标题流光效果 */
h1::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(0, 212, 255, 0.2), transparent);
  animation: shimmer 3s infinite;
}

@keyframes shimmer {
  0% { left: -100%; }
  100% { left: 100%; }
}

.dashboard-container {
  display: flex;
  flex: 1;
  overflow: hidden;
  min-height: 0;
  margin: 0 !important;
  padding: 0 !important;
  height: calc(100vh - 70px);
  background: rgba(0, 13, 36, 0.8);
}

.sidebar {
  width: 400px;
  min-width: 350px;
  background: rgba(0, 21, 41, 0.9);
  padding: 20px;
  overflow-y: auto;
  height: 100%;
  margin: 0 !important;
  border-right: 1px solid rgba(0, 212, 255, 0.2);
  box-shadow: 5px 0 15px rgba(0, 0, 0, 0.3);
}

.map-area {
  flex: 1;
  height: 100%;
  position: relative;
  margin: 0 !important;
  padding: 0 !important;
  min-width: 0;
  background: rgba(8, 24, 48, 0.5);
}

.loading {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  font-size: 18px;
  color: #00d4ff;
  background: rgba(0, 13, 36, 0.8);
  text-shadow: 0 0 5px rgba(0, 212, 255, 0.5);
}
</style>