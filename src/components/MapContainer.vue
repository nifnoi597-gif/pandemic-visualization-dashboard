<template>
  <div id="map-container">
    <div v-if="isLoading" class="map-loading">地图数据加载中...</div>
    <!-- 切换按钮 -->
    <div class="map-switcher">
      <button 
        @click="switchMapLibrary('leaflet')" 
        :class="{ active: currentLibrary === 'leaflet' }"
      >
        Leaflet 视图
      </button>
      <button 
        @click="switchMapLibrary('openlayers')" 
        :class="{ active: currentLibrary === 'openlayers' }"
      >
        OpenLayers 视图
      </button>
    </div>
  </div>
</template>

<script setup>
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { onMounted, inject, ref, watch, onUnmounted, nextTick } from 'vue';
import { Map, View } from 'ol';
import TileLayer from 'ol/layer/Tile';
import OSM from 'ol/source/OSM';
import VectorLayer from 'ol/layer/Vector';
import VectorSource from 'ol/source/Vector';
import { Circle as CircleStyle, Fill, Stroke, Style } from 'ol/style';
import { fromLonLat } from 'ol/proj';
import Feature from 'ol/Feature';
import Point from 'ol/geom/Point';

// 修复Leaflet图标路径问题
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// 从父组件获取数据和时间索引
const mockPandemicData = inject('pandemicData');
const currentTimeIndex = inject('currentTimeIndex');
const isLoading = inject('isLoading', ref(false));

// 地图库状态
const currentLibrary = ref('leaflet');
let leafletMap = null;
let openlayersMap = null;
let dynamicLayer = null;
let vectorSource = null;
let openlayersControls = [];
let leafletControls = [];

// 统一的半径计算因子，用于保持两个视图标记大小一致
const RADIUS_FACTOR = 0.8;

// 清除所有控件
const clearControls = () => {
  // 清除OpenLayers控件
  openlayersControls.forEach(control => {
    if (control && control.parentNode) {
      control.parentNode.removeChild(control);
    }
  });
  openlayersControls = [];
  
  // 清除Leaflet控件
  leafletControls.forEach(control => {
    if (leafletMap && control) {
      leafletMap.removeControl(control);
    }
  });
  leafletControls = [];
};

// 切换地图库
const switchMapLibrary = (library) => {
  if (currentLibrary.value === library) return;
  
  currentLibrary.value = library;
  
  // 清除当前地图和控件
  if (leafletMap) {
    leafletMap.remove();
    leafletMap = null;
  }
  if (openlayersMap) {
    openlayersMap.setTarget(null);
    openlayersMap = null;
  }
  
  clearControls();
  
  // 初始化新地图
  if (library === 'leaflet') {
    initLeafletMap();
  } else {
    initOpenLayersMap();
  }
};

// 初始化Leaflet地图
const initLeafletMap = () => {
  leafletMap = L.map('map-container', {
    zoomControl: false, // 禁用默认缩放控件
    attributionControl: false // 禁用默认版权控件
  }).setView([34, 108], 4);
  
  // 使用高德地图瓦片，不显示版权信息
  L.tileLayer('https://webrd0{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}', {
    subdomains: ['1', '2', '3', '4'],
    maxZoom: 20,
    attribution: '' // 移除版权信息
  }).addTo(leafletMap);

  dynamicLayer = L.layerGroup().addTo(leafletMap);
  
  // 添加统一控件
  addZoomControl();
  addTimeControl();
  addLegend();
  
  // 渲染数据
  if (mockPandemicData.value && mockPandemicData.value.length) {
    renderTimeData(currentTimeIndex.value);
  }
};

// 初始化OpenLayers地图
const initOpenLayersMap = () => {
  openlayersMap = new Map({
    target: 'map-container',
    layers: [
      new TileLayer({
        source: new OSM({
          attributions: [] // 移除默认版权信息
        })
      })
    ],
    view: new View({
      center: fromLonLat([108, 34]),
      zoom: 4
    }),
    controls: [] // 禁用所有默认控件
  });

  vectorSource = new VectorSource();
  const vectorLayer = new VectorLayer({
    source: vectorSource,
    style: function(feature) {
      const confirmed = feature.get('confirmed');
      let color = '#00ff00';
      if (confirmed > 2000) {
        color = '#ff0000';
      } else if (confirmed > 500) {
        color = '#ffa500';
      }

      // 使用统一的半径计算因子，与Leaflet保持一致
      return new Style({
        image: new CircleStyle({
          radius: Math.sqrt(confirmed) * RADIUS_FACTOR,
          fill: new Fill({
            color: color + 'CC'
          }),
          stroke: new Stroke({
            color: '#ffffff',
            width: 1
          })
        })
      });
    }
  });

  openlayersMap.addLayer(vectorLayer);
  
  // 等待DOM更新后添加统一控件
  nextTick(() => {
    addZoomControl();
    addTimeControl();
    addLegend();
  });
  
  // 渲染数据
  if (mockPandemicData.value && mockPandemicData.value.length) {
    renderTimeData(currentTimeIndex.value);
  }
};

// 统一添加缩放控件
const addZoomControl = () => {
  if (currentLibrary.value === 'leaflet' && leafletMap) {
    // 创建自定义Leaflet缩放控件
    const zoomControl = L.control({ position: 'topleft' });
    
    zoomControl.onAdd = function() {
      const div = L.DomUtil.create('div', 'zoom-control');
      div.innerHTML = `
        <div class="zoom-buttons">
          <button class="zoom-in">+</button>
          <button class="zoom-out">−</button>
        </div>
      `;
      
      // 添加事件监听
      div.querySelector('.zoom-in').addEventListener('click', () => {
        leafletMap.zoomIn();
      });
      
      div.querySelector('.zoom-out').addEventListener('click', () => {
        leafletMap.zoomOut();
      });
      
      return div;
    };
    
    zoomControl.addTo(leafletMap);
    leafletControls.push(zoomControl);
  } 
  else if (currentLibrary.value === 'openlayers' && openlayersMap) {
    const zoomControlDiv = document.createElement('div');
    zoomControlDiv.className = 'zoom-control';
    zoomControlDiv.innerHTML = `
      <div class="zoom-buttons">
        <button class="zoom-in">+</button>
        <button class="zoom-out">−</button>
      </div>
    `;
    
    document.getElementById('map-container').appendChild(zoomControlDiv);
    openlayersControls.push(zoomControlDiv);
    
    // 添加事件监听
    zoomControlDiv.querySelector('.zoom-in').addEventListener('click', () => {
      const view = openlayersMap.getView();
      view.animate({
        zoom: view.getZoom() + 1,
        duration: 250
      });
    });
    
    zoomControlDiv.querySelector('.zoom-out').addEventListener('click', () => {
      const view = openlayersMap.getView();
      view.animate({
        zoom: view.getZoom() - 1,
        duration: 250
      });
    });
  }
};

// 统一添加时间轴控件
const addTimeControl = () => {
  if (!mockPandemicData.value || !mockPandemicData.value.length) {
    setTimeout(() => addTimeControl(), 100);
    return;
  }
  
  const timelineLength = mockPandemicData.value[0]?.timeline?.length || 3;
  const firstDate = mockPandemicData.value[0]?.timeline?.[0]?.date || '2020-01-20';
  
  if (currentLibrary.value === 'leaflet' && leafletMap) {
    const timeControl = L.control({ position: 'bottomleft' });

    timeControl.onAdd = function () {
      const div = L.DomUtil.create('div', 'time-control');
      
      div.innerHTML = `
        <div class="time-control-content">
          <h4>时间轴控制</h4>
          <div class="time-slider-container">
            <input type="range" class="time-slider" min="0" max="${timelineLength - 1}" value="0" step="1">
            <span class="current-date">${firstDate}</span>
          </div>
          <div class="time-buttons">
            <button class="play-btn">播放</button>
            <button class="pause-btn">暂停</button>
          </div>
        </div>
      `;
      return div;
    };

    timeControl.addTo(leafletMap);
    leafletControls.push(timeControl);
    
    // 绑定事件
    bindTimeControlEvents(timeControl.getContainer());
  } 
  else if (currentLibrary.value === 'openlayers' && openlayersMap) {
    const controlDiv = document.createElement('div');
    controlDiv.className = 'time-control';
    controlDiv.innerHTML = `
      <div class="time-control-content">
        <h4>时间轴控制</h4>
        <div class="time-slider-container">
          <input type="range" class="time-slider" min="0" max="${timelineLength - 1}" value="0" step="1">
          <span class="current-date">${firstDate}</span>
        </div>
        <div class="time-buttons">
          <button class="play-btn">播放</button>
          <button class="pause-btn">暂停</button>
        </div>
      </div>
    `;
    
    document.getElementById('map-container').appendChild(controlDiv);
    openlayersControls.push(controlDiv);
    
    // 绑定事件
    bindTimeControlEvents(controlDiv);
  }
};

// 时间控件事件绑定（统一逻辑）
const bindTimeControlEvents = (container) => {
  let playInterval = null;
  const timeSlider = container.querySelector('.time-slider');
  const currentDateEl = container.querySelector('.current-date');
  const playBtn = container.querySelector('.play-btn');
  const pauseBtn = container.querySelector('.pause-btn');
  
  // 更新时间显示的函数
  const updateTimeDisplay = (index) => {
    if (!mockPandemicData.value.length) return;
    const sampleData = mockPandemicData.value[0].timeline[index];
    if (currentDateEl && timeSlider) {
      currentDateEl.textContent = sampleData.date;
      timeSlider.value = index;
    }
    currentTimeIndex.value = index;
  };

  // 滑块事件监听
  timeSlider.addEventListener('input', (e) => {
    const index = parseInt(e.target.value);
    currentTimeIndex.value = index;
    updateTimeDisplay(index);
    renderTimeData(index);
  });

  // 播放按钮事件
  playBtn.addEventListener('click', () => {
    if (playInterval) clearInterval(playInterval);
    
    const maxIndex = mockPandemicData.value[0].timeline.length - 1;
    playInterval = setInterval(() => {
      currentTimeIndex.value = (currentTimeIndex.value + 1) % (maxIndex + 1);
      updateTimeDisplay(currentTimeIndex.value);
      renderTimeData(currentTimeIndex.value);
      
      if (currentTimeIndex.value === maxIndex) {
        clearInterval(playInterval);
        playInterval = null;
      }
    }, 1000);
  });

  // 暂停按钮事件
  pauseBtn.addEventListener('click', () => {
    if (playInterval) {
      clearInterval(playInterval);
      playInterval = null;
    }
  });
};

// 统一添加图例
const addLegend = () => {
  if (currentLibrary.value === 'leaflet' && leafletMap) {
    const legend = L.control({ position: 'bottomright' });
    
    legend.onAdd = function () {
      const div = L.DomUtil.create('div', 'map-legend');
      div.innerHTML = `
        <div class="legend-content">
          <strong>疫情风险等级</strong>
          <div class="legend-item"><span class="legend-color" style="background-color: #00ff00;"></span> 0–500 例</div>
          <div class="legend-item"><span class="legend-color" style="background-color: #ffa500;"></span> 500–2000 例</div>
          <div class="legend-item"><span class="legend-color" style="background-color: #ff0000;"></span> 2000+ 例</div>
        </div>
      `;
      return div;
    };

    legend.addTo(leafletMap);
    leafletControls.push(legend);
  } 
  else if (currentLibrary.value === 'openlayers' && openlayersMap) {
    const legendDiv = document.createElement('div');
    legendDiv.className = 'map-legend';
    legendDiv.innerHTML = `
      <div class="legend-content">
        <strong>疫情风险等级</strong>
        <div class="legend-item"><span class="legend-color" style="background-color: #00ff00;"></span> 0–500 例</div>
        <div class="legend-item"><span class="legend-color" style="background-color: #ffa500;"></span> 500–2000 例</div>
        <div class="legend-item"><span class="legend-color" style="background-color: #ff0000;"></span> 2000+ 例</div>
      </div>
    `;
    
    document.getElementById('map-container').appendChild(legendDiv);
    openlayersControls.push(legendDiv);
  }
};

// 渲染函数
const renderTimeData = (timeIndex) => {
  if (isLoading.value) return;
  
  if (currentLibrary.value === 'leaflet') {
    renderLeafletData(timeIndex);
  } else {
    renderOpenLayersData(timeIndex);
  }
};

// Leaflet数据渲染
const renderLeafletData = (timeIndex) => {
  if (!dynamicLayer) return;
  
  dynamicLayer.clearLayers();
  
  mockPandemicData.value.forEach(city => {
    const data = city.timeline[timeIndex];
    if (!data) return;
    
    // 使用统一的半径计算因子
    const radius = Math.sqrt(data.confirmed) * RADIUS_FACTOR;
    let color = '#00ff00';
    if (data.confirmed > 2000) {
      color = '#ff0000';
    } else if (data.confirmed > 500) {
      color = '#ffa500';
    }

    const circle = L.circleMarker([city.lat, city.lon], {
      radius: radius,
      color: color,
      weight: 1,
      fillColor: color,
      fillOpacity: 0.6
    }).addTo(dynamicLayer);

    circle.bindPopup(`
      <div style="text-align: left;">
        <h3 style="margin: 5px 0;">${city.name} (${data.date})</h3>
        <b>确诊：</b> ${data.confirmed.toLocaleString()} 例<br>
        <b>死亡：</b> ${data.deaths} 例<br>
        <b>治愈：</b> ${data.recovered.toLocaleString()} 例
      </div>
    `);

    circle.on('mouseover', function(e) {
      this.openPopup();
      this.setStyle({ fillOpacity: 0.8 });
    });
    
    circle.on('mouseout', function(e) {
      this.setStyle({ fillOpacity: 0.6 });
    });
  });
};

// OpenLayers数据渲染
const renderOpenLayersData = (timeIndex) => {
  if (!vectorSource) return;
  
  vectorSource.clear();
  
  mockPandemicData.value.forEach(city => {
    const data = city.timeline[timeIndex];
    if (!data) return;
    
    const feature = new Feature({
      geometry: new Point(fromLonLat([city.lon, city.lat])),
      name: city.name,
      confirmed: data.confirmed,
      deaths: data.deaths,
      recovered: data.recovered,
      date: data.date
    });
    
    vectorSource.addFeature(feature);
  });
};

// 初始化
onMounted(() => {
  if (!isLoading.value) {
    initLeafletMap();
  }
});

// 数据监听
watch([isLoading, mockPandemicData], ([loading, data]) => {
  if (!loading && data && data.length) {
    if (currentLibrary.value === 'leaflet') {
      initLeafletMap();
    } else if (currentLibrary.value === 'openlayers') {
      initOpenLayersMap();
    }
  }
});

// 清理资源
onUnmounted(() => {
  if (leafletMap) {
    leafletMap.remove();
  }
  if (openlayersMap) {
    openlayersMap.setTarget(null);
  }
  clearControls();
});
</script>

<style scoped>
#map-container {
  height: 100% !important;
  width: 100% !important;
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  margin: 0 !important;
  padding: 0 !important;
}

.map-loading {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  font-size: 16px;
  color: #00d4ff;
  background: rgba(0, 13, 36, 0.8);
  text-shadow: 0 0 5px rgba(0, 212, 255, 0.5);
}

.map-switcher {
  position: absolute;
  top: 20px;
  right: 20px;
  z-index: 1001;
  display: flex;
  gap: 10px;
}

.map-switcher button {
  padding: 8px 16px;
  background: rgba(0, 21, 41, 0.9);
  border: 1px solid rgba(0, 212, 255, 0.3);
  color: #e8f4ff;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 12px;
}

.map-switcher button:hover {
  background: rgba(0, 212, 255, 0.2);
  border-color: rgba(0, 212, 255, 0.5);
}

.map-switcher button.active {
  background: rgba(0, 212, 255, 0.3);
  border-color: rgba(0, 212, 255, 0.7);
  box-shadow: 0 0 10px rgba(0, 212, 255, 0.3);
}

/* 统一缩放控件样式 */
:deep(.zoom-control) {
  position: absolute !important;
  top: 20px !important;
  left: 20px !important;
  z-index: 1000 !important;
  width: 36px !important;
  height: 64px !important;
}

:deep(.zoom-buttons) {
  background: rgba(0, 21, 41, 0.9);
  border-radius: 4px;
  box-shadow: 0 1px 5px rgba(0,0,0,0.4);
  border: 1px solid rgba(0, 212, 255, 0.3);
  overflow: hidden;
  width: 34px !important;
  height: 62px !important;
}

:deep(.zoom-control button) {
  display: block;
  width: 34px !important;
  height: 31px !important;
  background: transparent;
  border: none;
  color: #e8f4ff;
  font-size: 18px;
  font-weight: bold;
  cursor: pointer;
  padding: 0 !important;
  margin: 0 !important;
  line-height: 31px !important;
  text-align: center !important;
}

:deep(.zoom-in) {
  border-bottom: 1px solid rgba(0, 212, 255, 0.3) !important;
}

:deep(.zoom-control button:hover) {
  background: rgba(0, 212, 255, 0.2);
}

/* 统一时间轴控件样式 */
:deep(.time-control) {
  position: absolute !important;
  bottom: 80px !important;
  left: 20px !important;
  z-index: 1000 !important;
  font-family: 'Segoe UI', sans-serif;
  width: 340px !important;
}

:deep(.time-control-content) {
  background: linear-gradient(135deg, rgba(0, 21, 41, 0.9) 0%, rgba(0, 40, 77, 0.9) 100%);
  border: 1px solid rgba(0, 212, 255, 0.3);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
  border-radius: 8px;
  color: #e8f4ff;
  padding: 12px;
  width: 314px !important;
}

:deep(.time-control h4) {
  color: #00d4ff;
  text-shadow: 0 0 5px rgba(0, 212, 255, 0.5);
  margin: 0 0 12px 0;
  font-size: 14px;
  height: 18px !important;
}

:deep(.time-slider-container) {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
  width: 100% !important;
}

:deep(.time-slider) {
  flex: 1;
  max-width: 200px !important;
  height: 6px !important;
  background: rgba(0, 212, 255, 0.2);
  border-radius: 10px;
  margin: 0 !important;
  padding: 0 !important;
}

:deep(.current-date) {
  color: #8ac6ff;
  margin-left: 10px !important;
  min-width: 80px !important;
  text-align: center;
}

:deep(.time-buttons) {
  display: flex;
  gap: 8px;
}

:deep(.time-buttons button) {
  padding: 6px 12px !important;
  background: rgba(0, 212, 255, 0.2);
  border: 1px solid rgba(0, 212, 255, 0.3);
  color: #e8f4ff;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 12px !important;
  width: 60px !important;
  height: 30px !important;
  margin: 0 !important;
  box-sizing: border-box !important;
}

:deep(.time-buttons button:hover) {
  background: rgba(0, 212, 255, 0.3);
  border-color: rgba(0, 212, 255, 0.5);
}

/* 统一图例样式 */
:deep(.map-legend) {
  position: absolute !important;
  bottom: 20px !important;
  right: 20px !important;
  z-index: 1000 !important;
  line-height: 1.6;
  color: #e8f4ff;
  font-family: 'Segoe UI', sans-serif;
  width: 160px !important;
}

:deep(.legend-content) {
  background: linear-gradient(135deg, rgba(0, 21, 41, 0.9) 0%, rgba(0, 40, 77, 0.9) 100%);
  border: 1px solid rgba(0, 212, 255, 0.3);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
  border-radius: 8px;
  padding: 12px;
  width: 134px !important;
}

:deep(.legend-item) {
  margin: 5px 0 !important;
  display: flex;
  align-items: center;
  height: 22px !important;
}

:deep(.legend-color) {
  width: 18px !important;
  height: 18px !important;
  display: inline-block;
  margin-right: 8px !important;
  border-radius: 50%;
  box-shadow: 0 0 5px currentColor;
  vertical-align: middle;
  opacity: 0.9;
}

/* 确保Leaflet和OpenLayers默认版权控件被完全移除 */
:deep(.leaflet-control-attribution),
:deep(.ol-attribution) {
  display: none !important;
}

:deep(.leaflet-control),
:deep(.ol-control) {
  margin: 0 !important;
  padding: 0 !important;
}
</style>

