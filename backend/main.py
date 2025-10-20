import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum
import uvicorn
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Enum as SQLAlchemyEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session, joinedload

app = FastAPI()

# Настройки CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешаем все origins для разработки
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# --------------------- Основная база данных production_reports.db ---------------------
DATABASE_URL = "sqlite:///./production_reports.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    cement_produced = Column(Float)
    cement_plan = Column(Float)

    raw_materials = relationship("RawMaterialDB", back_populates="report")
    energy = relationship("EnergyConsumptionDB", uselist=False, back_populates="report")
    downtimes = relationship("DowntimeEventDB", back_populates="report")
    quality = relationship("QualityParametersDB", uselist=False, back_populates="report")
    attendance = relationship("AttendanceDB", back_populates="report")

class RawMaterialDB(Base):
    __tablename__ = "raw_materials"
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id"))
    resource_name = Column(String)
    fact_cons = Column(Float)
    plan_cons = Column(Float)
    report = relationship("Report", back_populates="raw_materials")

class EnergyConsumptionDB(Base):
    __tablename__ = "energy_consumption"
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id"))
    electricity = Column(Float)
    gas = Column(Float)
    water = Column(Float)
    report = relationship("Report", back_populates="energy")

class DowntimeEventDB(Base):
    __tablename__ = "downtime_events"
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id"))
    type_of_problem = Column(String)
    problem = Column(String)
    problem_start = Column(String)
    problem_stop = Column(String)
    report = relationship("Report", back_populates="downtimes")

class QualityParametersDB(Base):
    __tablename__ = "quality_parameters"
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id"))
    rav = Column(Float)
    density = Column(Float)
    humidity = Column(Float)
    report = relationship("Report", back_populates="quality")

class AttendanceDB(Base):
    __tablename__ = "attendance"
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id"))
    fio = Column(String)
    yavka = Column(Boolean)
    late = Column(String)
    narush = Column(String)
    report = relationship("Report", back_populates="attendance")

Base.metadata.create_all(bind=engine)

# --------------------- База данных cement_database.db ---------------------
Base2 = declarative_base()

class CementType(Base2):
    __tablename__ = 'cement_types'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(500))
    hardness = Column(Float)
    density = Column(Float)
    humidity = Column(Float)

    raw_materials = relationship("RawMaterialConsumption", back_populates="cement_type")
    energy_consumption = relationship("EnergyConsumption", back_populates="cement_type")

class RawMaterialConsumption(Base2):
    __tablename__ = 'raw_material_consumption'
    id = Column(Integer, primary_key=True, autoincrement=True)
    cement_type_id = Column(Integer, ForeignKey('cement_types.id'), nullable=False)
    limestone = Column(Float, nullable=False)
    clay = Column(Float, nullable=False)
    gypsum = Column(Float, nullable=False)
    cement_type = relationship("CementType", back_populates="raw_materials")

class EnergyConsumption(Base2):
    __tablename__ = 'energy_consumption'
    id = Column(Integer, primary_key=True, autoincrement=True)
    cement_type_id = Column(Integer, ForeignKey('cement_types.id'), nullable=False)
    electricity = Column(Float, nullable=False)
    gas = Column(Float, nullable=False)
    water = Column(Float, nullable=False)
    cement_type = relationship("CementType", back_populates="energy_consumption")

engine2 = create_engine('sqlite:///./cement_database.db', connect_args={"check_same_thread": False})
Session2 = sessionmaker(autocommit=False, autoflush=False, bind=engine2)
Base2.metadata.create_all(engine2)

# --------------------- База данных shifts.db ---------------------
Base3 = declarative_base()

class EmployeeRole(str, Enum):
    WORKER = "worker"
    MANAGER = "manager"
    ADMIN = "admin"

class BuildingDB(Base3):
    __tablename__ = "buildings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)

class EmployeeDB(Base3):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    birth_date = Column(DateTime, nullable=False)
    role = Column(SQLAlchemyEnum(EmployeeRole), nullable=False)
    password = Column(String, nullable=False)
    workplace_id = Column(Integer, ForeignKey('buildings.id'))
    workplace = relationship("BuildingDB")

class ShiftDB(Base3):
    __tablename__ = "shifts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    head_of_shift = Column(Integer)

class ShiftEmployeeDB(Base3):
    __tablename__ = "shift_employees"
    shift_id = Column(Integer, ForeignKey('shifts.id'), primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), primary_key=True)
    employee = relationship("EmployeeDB")

engine3 = create_engine("sqlite:///./shift.db", connect_args={"check_same_thread": False})
Session3 = sessionmaker(autocommit=False, autoflush=False, bind=engine3)
Base3.metadata.create_all(bind=engine3)

# --------------------- Pydantic модели ---------------------
class RawMaterial(BaseModel):
    resource_name: str
    fact_cons: float
    plan_cons: float


class EnergyConsumptionRequest(BaseModel):
    electricity: float
    gas: float
    water: float


class DowntimeEvent(BaseModel):
    type_of_problem: str
    problem: str
    problem_start: str
    problem_stop: str


class QualityParameters(BaseModel):
    rav: float
    density: float
    humidity: float


class ShiftAttendance(BaseModel):
    employee_name: str
    shift_start: datetime
    shift_end: datetime
    yavka: bool
    late: Optional[str] = None
    narush: Optional[str] = None


class Attendance(BaseModel):
    shift: str
    fio: str
    yavka: bool
    late: str
    narush: str


class ReportData(BaseModel):
    cement_produced: int
    cement_plan: int
    downtime: List[DowntimeEvent]  # Указываем тип для downtime
    energy_consumption: EnergyConsumptionRequest  # Указываем тип для energy_consumption
    quality: QualityParameters  # Указываем тип для quality
    raw_materials: List[RawMaterial]  # Указываем тип для raw_materials
    attendance: List[Attendance]  # Указываем тип для attendance


class RawMaterialConsumptionResponse(BaseModel):
    id: int
    cement_type_id: int
    limestone: float
    clay: float
    gypsum: float

    class Config:
        from_attributes = True


class EnergyConsumptionResponse(BaseModel):
    id: int
    cement_type_id: int
    electricity: float
    gas: float
    water: float

    class Config:
        from_attributes = True


class CementTypeResponse(BaseModel):
    id: int
    name: str
    description: str
    hardness: float
    density: float
    humidity: float
    raw_materials: RawMaterialConsumptionResponse
    energy_consumption: EnergyConsumptionResponse

    class Config:
        from_attributes = True


class CementDataResponse(BaseModel):
    cement_types: List[CementTypeResponse]


class ShiftInfo(BaseModel):
    employee_name: str
    shift_start: datetime
    shift_end: datetime


class ShiftDataResponse(BaseModel):
    shifts: List[ShiftInfo]

# --------------------- Dependency ---------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_cement_db():
    db = Session2()
    try:
        yield db
    finally:
        db.close()

def get_shift_db():
    db = Session3()
    try:
        yield db
    finally:
        db.close()

# --------------------- Эндпоинты ---------------------
@app.get("/")
async def root():
    return {"message": "Cement Production Reporting System"}

@app.post("/reports")
async def create_report(data: ReportData, db: Session = Depends(get_db)):
    try:
        # Create main report
        report = Report(
            cement_produced=data.cement_produced,
            cement_plan=data.cement_plan
        )
        db.add(report)
        db.commit()
        db.refresh(report)

        # Process raw materials data
        for material in data.raw_materials:
            db.add(RawMaterialDB(
                report_id=report.id,
                resource_name=material.resource_name,
                fact_cons=material.fact_cons,
                plan_cons=material.plan_cons
            ))

        # Process energy consumption data
        db.add(EnergyConsumptionDB(
            report_id=report.id,
            electricity=data.energy_consumption.electricity,
            gas=data.energy_consumption.gas,
            water=data.energy_consumption.water
        ))

        # Process downtime events
        for downtime in data.downtime:
            db.add(DowntimeEventDB(
                report_id=report.id,
                type_of_problem=downtime.type_of_problem,
                problem=downtime.problem,
                problem_start=downtime.problem_start,
                problem_stop=downtime.problem_stop
            ))

        # Process quality parameters
        db.add(QualityParametersDB(
            report_id=report.id,
            rav=data.quality.rav,
            density=data.quality.density,
            humidity=data.quality.humidity
        ))

        # Process attendance data
        for attendance in data.attendance:
            db.add(AttendanceDB(
                report_id=report.id,
                fio=attendance.fio,
                yavka=attendance.yavka,
                late=attendance.late,
                narush=attendance.narush
            ))

        db.commit()
        return {"message": "Report created successfully", "report_id": report.id}
    
    except Exception as e:
        db.rollback()
        print(f"Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/cement-data", response_model=CementDataResponse)
async def get_all_cement_data(db: Session = Depends(get_cement_db)):
    try:
        cement_types = db.query(CementType)\
            .options(
                joinedload(CementType.raw_materials),
                joinedload(CementType.energy_consumption)
            )\
            .all()

        result = []
        for ct in cement_types:
            if not ct.raw_materials or not ct.energy_consumption:
                continue

            cement_type_data = CementTypeResponse(
                id=ct.id,
                name=ct.name,
                description=ct.description or "",
                hardness=ct.hardness,
                density=ct.density,
                humidity=ct.humidity,
                raw_materials=ct.raw_materials[0],
                energy_consumption=ct.energy_consumption[0]
            )
            result.append(cement_type_data)
        
        return {"cement_types": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching cement data: {str(e)}")

@app.get("/shift-data", response_model=ShiftDataResponse)
async def get_shift_data(db: Session = Depends(get_shift_db)):
    try:
        shifts = db.query(ShiftDB).all()
        result = []
        for shift in shifts:
            employees = db.query(ShiftEmployeeDB).filter(ShiftEmployeeDB.shift_id == shift.id).all()
            for emp in employees:
                employee = db.query(EmployeeDB).filter(EmployeeDB.id == emp.employee_id).first()
                if employee:
                    result.append(ShiftInfo(
                        employee_name=employee.name,
                        shift_start=shift.start_time,
                        shift_end=shift.end_time
                    ))
        return {"shifts": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching shift data: {str(e)}")


# --------------------- Запуск приложения ---------------------
if __name__ == "__main__":
    uvicorn.run("main:app", port=3000, reload=True)