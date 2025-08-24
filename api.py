from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
from datetime import datetime, timedelta
import random

app = FastAPI(title="疫情数据API")

# 允许前端跨域访问 - 修改这部分
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 改为允许所有来源，或者指定具体端口
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# # 或者更精确的配置（推荐）
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=[
#         "http://localhost:5173",
#         "http://localhost:5174",  # 添加你实际使用的端口
#         "http://127.0.0.1:5173",
#         "http://127.0.0.1:5174"   # 添加你实际使用的端口
#     ],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

def generate_realistic_data():
    cities = [
        {"name": "北京", "lat": 39.9042, "lon": 116.4074},
        {"name": "上海", "lat": 31.2304, "lon": 121.4737},
        {"name": "广州", "lat": 23.1291, "lon": 113.2644},
        {"name": "深圳", "lat": 22.3193, "lon": 114.1694},
        {"name": "武汉", "lat": 30.5928, "lon": 114.3055},
        {"name": "西安", "lat": 34.3416, "lon": 108.9398},
        {"name": "成都", "lat": 30.5728, "lon": 104.0668},
        {"name": "杭州", "lat": 30.2741, "lon": 120.1551},
        {"name": "南京", "lat": 32.0603, "lon": 118.7969},
        {"name": "郑州", "lat": 34.7466, "lon": 113.6253}
    ]
    
    # 修改为2020年1月-2月的时间序列（疫情爆发期）
    timeline = []
    base_date = datetime(2020, 1, 20)  # 疫情开始受到广泛关注的时间
    for i in range(30):  # 生成30天数据
        date = (base_date + timedelta(days=i)).strftime("%Y-%m-%d")
        timeline.append(date)
    
    result = []
    for city in cities:
        city_data = {
            "name": city["name"],
            "lat": city["lat"],
            "lon": city["lon"],
            "timeline": []
        }
        
        # 为每个城市生成更真实的新冠疫情增长趋势
        # 武汉作为疫情中心，数据量最大
        if city["name"] == "武汉":
            base_confirmed = random.randint(500, 1000)  # 武汉起始数据较大
        else:
            base_confirmed = random.randint(10, 100)   # 其他城市起始数据较小
        
        for i, date in enumerate(timeline):
            # 模拟疫情爆发期的指数增长
            growth_factor = 1 + (i * 0.3)  # 更陡峭的增长曲线
            confirmed = int(base_confirmed * growth_factor * (1 + random.random() * 0.5))
            deaths = max(0, int(confirmed * 0.03 + random.randint(-2, 3)))  # 死亡率略高
            recovered = max(0, int(confirmed * 0.2 + random.randint(-10, 15)))  # 初期治愈率较低
            
            city_data["timeline"].append({
                "date": date,
                "confirmed": confirmed,
                "deaths": deaths,
                "recovered": recovered
            })
        
        result.append(city_data)
    
    return result

@app.get("/")
async def root():
    return {"message": "疫情数据API服务已启动"}

@app.get("/api/pandemic-data")
async def get_pandemic_data():
    """获取疫情数据"""
    data = generate_realistic_data()
    return data

@app.get("/api/stats")
async def get_stats():
    """获取统计信息"""
    data = generate_realistic_data()
    total_confirmed = sum(city["timeline"][-1]["confirmed"] for city in data)
    total_deaths = sum(city["timeline"][-1]["deaths"] for city in data)
    total_recovered = sum(city["timeline"][-1]["recovered"] for city in data)
    
    return {
        "total_confirmed": total_confirmed,
        "total_deaths": total_deaths,
        "total_recovered": total_recovered,
        "last_updated": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)