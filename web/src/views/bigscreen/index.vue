<template>
  <div class="bigscreen-container">
    <!-- 顶部欢迎与时间 -->
    <div class="header">
      <div class="title">学生处热烈欢迎新同学入学！</div>
      <div class="datetime">{{ currentTime }}</div>
    </div>
    <div class="main-content">
      <!-- 左侧：各学院报到情况 -->
      <div class="left-panel">
        <div class="panel-title">各学院报到情况</div>
        <div class="college-list">
          <div v-for="(item, idx) in collegeList" :key="item.name" class="college-item">
            <div class="college-row1">
              <span class="college-name">{{ item.name }}</span>
              <span class="college-percent">{{ item.percent.toFixed(2) }}%</span>
            </div>
            <div class="college-row2">
              <div class="college-progress-bg">
                <div :style="{
                  width: item.percent + '%',
                  height: '100%',
                  borderRadius: '4px',
                  background: getProgressColor(item.percent),
                  transition: 'width 1.2s cubic-bezier(.4,2.3,.3,1)'
                }"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <!-- 中间：地图与统计 -->
      <div class="center-panel">
        <div class="stat-cards">
          <div class="stat-card" v-for="(item, idx) in statList" :key="item.label">
            <div class="stat-label">{{ item.label }}</div>
            <div class="stat-value">{{ item.value }}</div>
            <div class="stat-desc">完成情况：{{ item.percent }}%</div>
            <el-progress :percentage="item.percent" :stroke-width="8" :show-text="false" />
          </div>
        </div>
        <div class="map-panel">
          <div ref="chinaMap" class="echarts-map"></div>
        </div>
      </div>
      <!-- 右侧：性别、民族统计 -->
      <div class="right-panel">
        <div class="panel-title">新生性别统计</div>
        <div ref="genderChart" class="echarts-bar"></div>
        <div class="panel-title">新生民族统计</div>
        <div ref="nationChart" class="echarts-pie"></div>
        <div class="panel-title">民族分布</div>
        <div ref="nationPie" class="echarts-pie"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import dayjs from 'dayjs'

const currentTime = ref(dayjs().format('YYYY年MM月DD日 HH:mm:ss'))
setInterval(() => {
  currentTime.value = dayjs().format('YYYY年MM月DD日 HH:mm:ss')
}, 1000)

// 动态数字动画
function useAnimatedNumber(target, duration = 1200) {
  const val = ref(0)
  let start = 0
  let startTime = null
  function animate(ts) {
    if (!startTime) startTime = ts
    const progress = Math.min((ts - startTime) / duration, 1)
    val.value = Math.floor(start + (target - start) * progress)
    if (progress < 1) {
      requestAnimationFrame(animate)
    } else {
      val.value = target
    }
  }
  requestAnimationFrame(animate)
  return val
}

const collegeListRaw = [
  { name: '文法学院', percent: 10.99 },
  { name: '马克思主义学院', percent: 20.99 },
  { name: '外国语学院', percent: 30.99 },
  { name: '艺术学院', percent: 40.99 },
  { name: '工商管理学院', percent: 56.99 },
  { name: '理学院', percent: 56.99 },
  { name: '资源与土木工程学院', percent: 78.99 },
  { name: '冶金学院', percent: 89.99 },
  { name: '材料科学与工程学院', percent: 65.99 },
  { name: '机械工程与自动化学院', percent: 54.99 },
  { name: '信息科学与工程学院', percent: 67.99 },
  { name: '计算机科学与工程学院', percent: 98.99 },
  { name: '软件学院', percent: 100 },
  { name: '医学院与生物工程学院', percent: 8.65 },
  { name: '体育部', percent: 34.56 },
  { name: '民族教育学院', percent: 85.64 },
]
const collegeList = ref(collegeListRaw.map(i => ({ ...i, percent: 0 })))

const statListRaw = [
  { label: '实际报到人数', value: 4917, percent: 99.56 },
  { label: '南湖校区', value: 3043, percent: 56.33 },
  { label: '浑南校区', value: 1931, percent: 12.56 },
]
const statList = ref(statListRaw.map(i => ({ ...i, value: 0, percent: 0 })))

const chinaMap = ref(null)
const genderChart = ref(null)
const nationChart = ref(null)
const nationPie = ref(null)

onMounted(async () => {
  // 动态加载中国地图 geoJSON
  const res = await fetch('/china.geo.json')
  const geoJson = await res.json()
  echarts.registerMap('china', geoJson)
  // 数字动画
  statListRaw.forEach((item, idx) => {
    const num = useAnimatedNumber(item.value, 1200 + idx * 200)
    const per = useAnimatedNumber(Math.round(item.percent), 1200 + idx * 200)
    num.value = 0
    per.value = 0
    const update = () => {
      statList.value[idx].value = num.value
      statList.value[idx].percent = per.value
      if (num.value < item.value || per.value < Math.round(item.percent)) {
        requestAnimationFrame(update)
      }
    }
    update()
  })
  // 进度条动画
  collegeListRaw.forEach((item, idx) => {
    setTimeout(() => {
      useAnimatedNumber(item.percent, 1200 + idx * 30).value = item.percent
      collegeList.value[idx].percent = 0
      const animate = (ts) => {
        if (!collegeList.value[idx]._start) collegeList.value[idx]._start = ts
        const progress = Math.min((ts - collegeList.value[idx]._start) / 1200, 1)
        collegeList.value[idx].percent = +(item.percent * progress).toFixed(2)
        if (progress < 1) {
          requestAnimationFrame(animate)
        } else {
          collegeList.value[idx].percent = item.percent
        }
      }
      requestAnimationFrame(animate)
    }, idx * 60)
  })
  // 地图
  nextTick(() => {
    const mapChart = echarts.init(chinaMap.value)
    mapChart.setOption({
      tooltip: {},
      visualMap: {
        min: 0,
        max: 1000,
        left: 'left',
        top: 'bottom',
        text: ['高','低'],
        inRange: { color: ['#005ce6', '#80aaff', '#e699ff', '#d24dff', '#cc33ff', '#9933ff'] },
        calculable: true
      },
      series: [{
        name: '报到人数',
        type: 'map',
        map: 'china',
        roam: true,
        label: { show: false },
        // 新增以下两行
        layoutCenter: ['50%', '52%'], // 地图中心点
        layoutSize: '120%',            // 地图大小占容器百分比
        data: [
          { name: '辽宁', value: 1410 },
          { name: '吉林', value: 939 },
          { name: '黑龙江', value: 537 },
          { name: '山东', value: 1069 },
          { name: '河北', value: 872 },
          { name: '山西', value: 522 },
          { name: '江苏', value: 797 },
          { name: '浙江', value: 454 },
          { name: '上海', value: 187 },
          { name: '广东', value: 579 },
          { name: '广西', value: 197 },
          { name: '四川', value: 578 },
          { name: '重庆', value: 187 },
          { name: '北京', value: 272 },
          { name: '天津', value: 106 },
          { name: '河南', value: 939 },
          { name: '湖北', value: 797 },
          { name: '湖南', value: 454 },
          { name: '江西', value: 187 },
          { name: '福建', value: 579 },
          { name: '安徽', value: 197 },
          { name: '陕西', value: 578 },
          { name: '甘肃', value: 187 },
          { name: '新疆', value: 100 },
          { name: '内蒙古', value: 100 },
        ]
      }]
    })
    // 性别统计
    echarts.init(genderChart.value).setOption({
      xAxis: { type: 'category', data: ['女生', '男生'], axisLabel: { color: '#6ad7ff', fontWeight: 'bold', fontSize: 16 }, axisLine: { lineStyle: { color: '#3b6dd8' } } },
      yAxis: { axisLabel: { color: '#6ad7ff' }, splitLine: { lineStyle: { color: '#233a5b' } } },
      series: [{
        data: [300, 200],
        type: 'bar',
        itemStyle: { color: (params) => params.dataIndex === 0 ? '#6ad7ff' : '#3b6dd8', shadowColor: '#6ad7ff', shadowBlur: 10 },
        barWidth: 40,
        label: { show: true, position: 'top', color: '#fff', fontWeight: 'bold', fontSize: 18 }
      }],
      grid: { left: 20, right: 20, top: 30, bottom: 20 }
    })
    // 民族统计
    echarts.init(nationChart.value).setOption({
      series: [{
        type: 'pie',
        radius: ['60%', '80%'],
        avoidLabelOverlap: false,
        label: { show: false },
        emphasis: { label: { show: true, fontSize: '18', fontWeight: 'bold', color: '#6ad7ff' } },
        data: [
          { value: 7.14, name: '满族', itemStyle: { color: '#6ad7ff' } },
          { value: 92.86, name: '其他', itemStyle: { color: '#3b6dd8' } }
        ]
      }],
      color: ['#6ad7ff', '#3b6dd8'],
      backgroundColor: 'transparent'
    })
    // 民族分布
    echarts.init(nationPie.value).setOption({
      series: [{
        type: 'pie',
        radius: '80%',
        data: [
          { value: 100, name: '少数民族', itemStyle: { color: '#6ad7ff' } },
          { value: 100, name: '汉族', itemStyle: { color: '#3b6dd8' } }
        ],
        label: { color: '#fff', fontWeight: 'bold', fontSize: 16 }
      }],
      color: ['#6ad7ff', '#3b6dd8'],
      backgroundColor: 'transparent'
    })
  })
})

function getProgressColor(percent) {
  if (percent >= 90) return 'linear-gradient(90deg, #00ffe7 0%, #3b6dd8 100%)';
  if (percent >= 70) return 'linear-gradient(90deg, #4d4dff 0%, #00ffe7 100%)';
  if (percent >= 40) return 'linear-gradient(90deg, #4d4dff 0%, #cc00ff 100%)';
  return 'linear-gradient(90deg, #cc00ff 0%, #4d4dff 100%)';
}
</script>

<style scoped>
.bigscreen-container {
  width: 100vw;
  height: 100vh;
  background: #020716 !important;
  color: #eaf6ff;
  overflow: hidden !important;
  display: flex;
  flex-direction: column;
  font-family: 'Inter', 'Microsoft YaHei', Arial, sans-serif;
}
.header {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 40px 0 40px;
  font-size: 32px;
  font-weight: bold;
  letter-spacing: 2px;
  color: #6ad7ff;
  text-shadow: 0 0 2px #1e90ff33, 0 0 1px #fff2;
  border-bottom: 2px solid rgba(106,215,255,0.2);
  box-shadow: 0 2px 16px 0 rgba(0,255,255,0.08);
  background: rgba(20, 40, 80, 0.95);
  border-radius: 0 0 18px 18px;
  margin-bottom: 18px;
}
.title {
  color: #fff;
  text-shadow: 0 0 3px #3b6dd855, 0 0 1px #fff2;
  font-size: 28px;
  font-weight: 900;
}
.datetime {
  font-size: 20px;
  font-weight: 600;
  color: #6ad7ff;
  text-shadow: 0 0 2px #1e90ff33;
}
.main-content {
  flex: 1;
  display: grid;
  grid-template-columns: 340px 1fr 340px;
  gap: 32px;
  padding: 0 40px 32px 40px;
  height: 100%;
}
.left-panel, .right-panel {
  background: rgba(20,40,80,0.08);
  border-radius: 18px;
  padding: 28px 18px 28px 18px;
  display: flex;
  flex-direction: column;
  gap: 24px;
  border: 2px solid;
  border-image: linear-gradient(120deg, #00ffe7 10%, #3b6dd8 60%, #cc00ff 100%) 1;
  position: relative;
  min-height: 0;
  height: 100%;
  justify-content: space-between;
}
.left-panel::before, .right-panel::before {
  content: '';
  position: absolute;
  left: 0; top: 0; right: 0; bottom: 0;
  border-radius: 18px;
  pointer-events: none;
  /* box-shadow: 0 0 12px 2px #6ad7ff18 inset; */
}
.center-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 32px;
  min-width: 0;
}
.stat-cards {
  display: flex;
  gap: 32px;
}
.stat-card {
  background: rgba(20,40,80,0.08); /* 几乎透明 */
  border-radius: 16px;
  padding: 18px 32px;
  min-width: 220px;
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  /* box-shadow: 0 0 8px 0 #6ad7ff22, 0 0 1px #fff1; */
  border: 2px solid;
  border-image: linear-gradient(120deg, #00ffe7 10%, #3b6dd8 60%, #cc00ff 100%) 1;
  position: relative;
}
.stat-card::before {
  content: '';
  position: absolute;
  left: 0; top: 0; right: 0; bottom: 0;
  border-radius: 16px;
  pointer-events: none;
  /* box-shadow: 0 0 8px 1px #6ad7ff10 inset; */
}
.stat-label {
  font-size: 18px;
  margin-bottom: 8px;
  color: #6ad7ff;
  text-shadow: 0 0 2px #1e90ff33;
  font-weight: 700;
}
.stat-value {
  font-size: 40px;
  font-weight: bold;
  color: #ffe066;
  text-shadow: 0 0 3px #3b6dd855, 0 0 1px #fff2;
}
.stat-desc {
  font-size: 15px;
  margin-bottom: 8px;
  color: #6ad7ff;
  font-weight: 600;
}
.map-panel {
  flex: 1;
  background: rgba(20,40,80,0.08); /* 几乎透明 */
  border-radius: 16px;
  margin-top: 20px;
  min-height: 420px;
  /* box-shadow: 0 0 10px 0 #1e90ff22, 0 0 1px #fff1; */
  border: 2px solid;
  border-image: linear-gradient(120deg, #00ffe7 10%, #3b6dd8 60%, #cc00ff 100%) 1;
  position: relative;
}
.echarts-map {
  width: 100%;
  height: 100%;
}
.echarts-bar, .echarts-pie {
  width: 100%;
  height: 200px;
  margin-bottom: 24px;
  background: transparent;
  border-radius: 12px;
}
.college-list {
  display: flex;
  flex-direction: column;
  gap: 3px;
  flex: 1 1 0;
  height: 100%;
  justify-content: space-between;
  overflow-y: auto;
}
.college-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 16px;
  color: #eaf6ff;
  text-shadow: 0 0 1px #3b6dd833;
  font-weight: 500;
}
.college-row1 {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.college-name {
  min-width: 90px;
  font-size: 18px;
  color: #eaf6ff;
  font-weight: 500;
}
.college-percent {
  min-width: 48px;
  text-align: right;
  color: #6ad7ff;
  font-size: 16px;
  font-weight: bold;
}
.college-row2 {
  width: 100%;
  margin: 0 0 2px 0;
}
.college-progress-bg {
  width: 100%;
  height: 8px;
  border-radius: 4px;
  background: #232a4a;
  overflow: hidden;
}
.panel-title {
  font-size: 20px;
  font-weight: bold;
  margin-bottom: 16px;
  color: #6ad7ff;
  text-shadow: 0 0 2px #1e90ff33;
  border-left: 4px solid #6ad7ff;
  padding-left: 10px;
}
::v-deep .el-progress-bar__outer {
  background: #1a2a4a !important;
  border-radius: 8px !important;
}
::v-deep .el-progress-bar__inner {
  background: linear-gradient(90deg, #6ad7ff 0%, #ffe066 100%) !important;
  box-shadow: 0 0 8px #6ad7ff, 0 0 2px #fff;
  transition: width 1.2s cubic-bezier(.4,2.3,.3,1) !important;
}
::v-deep .el-progress {
  margin: 0 8px;
}
/* 自定义滚动条 */
.college-list::-webkit-scrollbar {
  width: 8px;
}
.college-list::-webkit-scrollbar-track {
  background: #374151;
  border-radius: 10px;
}
.college-list::-webkit-scrollbar-thumb {
  background: #4B5563;
  border-radius: 10px;
}
.college-list::-webkit-scrollbar-thumb:hover {
  background: #6B7280;
}
.right-panel > div {
  flex: 1 1 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
</style> 