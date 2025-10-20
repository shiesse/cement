import React, { useState, useEffect } from 'react';
import './ReportScreen.css';

function ReportScreen() {
  const [cementTypes, setCementTypes] = useState([]);
  const [selectedCementType, setSelectedCementType] = useState(null);
  const [cementProduced, setCementProduced] = useState(0);
  const [cementPlan, setCementPlan] = useState(0);
  const [rawMaterials, setRawMaterials] = useState([
    { resource_name: 'Известняк', fact_cons: 0, plan_cons: 0 },
    { resource_name: 'Глина', fact_cons: 0, plan_cons: 0 },
    { resource_name: 'Гипс', fact_cons: 0, plan_cons: 0 },
  ]);
  const [energyConsumption, setEnergyConsumption] = useState({
    electricity: 0,
    gas: 0,
    water: 0,
  });
  const [downtime, setDowntime] = useState([]);
  const [quality, setQuality] = useState({
    rav: 0,
    density: 0,
    humidity: 0,
  });
  const [attendanceByShift, setAttendanceByShift] = useState([]);
  
  useEffect(() => {
    async function fetchInitialData() {
      try {
        const [cementResponse, shiftResponse] = await Promise.all([
          fetch('http://127.0.0.1:3000/cement-data'),
          fetch('http://localhost:3000/shift-data'),
        ]);
  
        const cementData = await cementResponse.json();
        const shiftData = await shiftResponse.json();
  
        setCementTypes(cementData.cement_types);
  
        // Проверяем, что shiftData.shifts существует и имеет формат массива
        if (shiftData && Array.isArray(shiftData.shifts)) {
          const formattedShifts = shiftData.shifts.map((shift, idx) => ({
            shift_name: `${shift.employee_name} (${shift.shift_start} - ${shift.shift_end})`,  // Используем имя сотрудника и время смены
            employees: [{
              name: shift.employee_name,
              present: false,
              late: '',
              violations: '',
            }],
          }));
  
          setAttendanceByShift(formattedShifts);
        } else {
          console.error("Неверный формат данных по сменам:", shiftData);
          setAttendanceByShift([]); // Устанавливаем пустой массив, если данные невалидны
        }
      } catch (error) {
        console.error('Ошибка при загрузке данных:', error);
      }
    }
  
    fetchInitialData();
  }, []);
  
  useEffect(() => {
    if (selectedCementType) {
      const newRawMaterials = [...rawMaterials];
  
      newRawMaterials[0].fact_cons = (selectedCementType.raw_materials.limestone * cementProduced) / 1000;
      newRawMaterials[1].fact_cons = (selectedCementType.raw_materials.clay * cementProduced) / 1000;
      newRawMaterials[2].fact_cons = (selectedCementType.raw_materials.gypsum * cementProduced) / 1000;
  
      newRawMaterials[0].plan_cons = (selectedCementType.raw_materials.limestone * cementPlan) / 1000;
      newRawMaterials[1].plan_cons = (selectedCementType.raw_materials.clay * cementPlan) / 1000;
      newRawMaterials[2].plan_cons = (selectedCementType.raw_materials.gypsum * cementPlan) / 1000;
  
      setRawMaterials(newRawMaterials);
  
      setEnergyConsumption({
        electricity: (selectedCementType.energy_consumption.electricity * cementProduced) / 1000,
        gas: (selectedCementType.energy_consumption.gas * cementProduced) / 1000,
        water: (selectedCementType.energy_consumption.water * cementProduced) / 1000,
      });
  
      setQuality({
        rav: selectedCementType.hardness,
        density: selectedCementType.density,
        humidity: selectedCementType.humidity,
      });
    }
  }, [selectedCementType, cementProduced, cementPlan, rawMaterials]);

  const handleAddDowntime = () => {
    setDowntime([...downtime, { type_of_problem: '', problem: '', problem_start: '', problem_stop: '' }]);
  };

  const handleCementTypeChange = (e) => {
    const selectedId = parseInt(e.target.value);
    const cementType = cementTypes.find(type => type.id === selectedId);
    setSelectedCementType(cementType);
  };

  async function handleSaveReport() {
    const attendanceFlattened = attendanceByShift.flatMap(shift =>
      shift.employees.map(emp => ({
        shift: shift.shift_name,
        fio: emp.name,
        yavka: emp.present,
        late: emp.late,
        narush: emp.violations,
      }))
    );

    const reportData = {
      cement_produced: cementProduced,
      cement_plan: cementPlan,
      raw_materials: rawMaterials.map(material => ({
        resource_name: material.resource_name,
        fact_cons: material.fact_cons,
        plan_cons: material.plan_cons,
      })),
      energy_consumption: {
        electricity: energyConsumption.electricity,
        gas: energyConsumption.gas,
        water: energyConsumption.water,
      },
      downtime: downtime.map(item => ({
        type_of_problem: item.type_of_problem,
        problem: item.problem,
        problem_start: item.problem_start,
        problem_stop: item.problem_stop,
      })),
      quality: {
        rav: quality.rav,
        density: quality.density,
        humidity: quality.humidity,
      },
      attendance: attendanceFlattened,
    };

    console.log('Отправляемые данные отчета:', reportData);

    const response = await fetch('http://localhost:3000/reports', { // Corrected URL
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(reportData),
    });
    

    if (response.ok) {
      console.log('Отчет успешно отправлен');
      alert('Отчет успешно сохранен!');
    } else {
      console.error('Ошибка при отправке отчета');
      alert('Ошибка при сохранении отчета!');
    }
  }

  return (
    <div className="ReportScreen">
      <header className="ReportScreen-header">
        <h1>Отчет по производственным показателям</h1>
      </header>

      <section>
        <h2>Производственные показатели</h2>
        <div>
          <h3>Вид цемента</h3>
          <select onChange={handleCementTypeChange}>
            <option value="">Выберите вид цемента</option>
            {cementTypes.map(type => (
              <option key={type.id} value={type.id}>{type.name}</option>
            ))}
          </select>
          {selectedCementType && (
            <div className="cement-type-info">
              <p><strong>Описание:</strong> {selectedCementType.description}</p>
              <p><strong>Параметры:</strong> Твердость {selectedCementType.hardness} МПа, 
                Плотность {selectedCementType.density} кг/м³, 
                Влажность {selectedCementType.humidity}%</p>
            </div>
          )}
        </div>

        <div>
          <h3>Производство цемента</h3>
          <label>Произведено цемента, тонн:
            <input
              type="number"
              value={cementProduced}
              onChange={(e) => setCementProduced(Number(e.target.value))}
            />
          </label>
          <label>План производства, тонн:
            <input
              type="number"
              value={cementPlan}
              onChange={(e) => setCementPlan(Number(e.target.value))}
            />
          </label>
        </div>

        <div>
          <h3>Потребление сырья</h3>
          <table>
            <thead>
              <tr>
                <th>Название сырья</th>
                <th>Фактический расход (тонн)</th>
                <th>Плановый расход (тонн)</th>
              </tr>
            </thead>
            <tbody>
              {rawMaterials.map((material, idx) => (
                <tr key={idx}>
                  <td>{material.resource_name}</td>
                  <td><input type="number" value={material.fact_cons.toFixed(2)} readOnly /></td>
                  <td><input type="number" value={material.plan_cons.toFixed(2)} readOnly /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div>
          <h3>Расход энергоресурсов</h3>
          <label>Электричество (кВт·ч):
            <input type="number" value={energyConsumption.electricity.toFixed(2)} readOnly />
          </label>
          <label>Газ (м³):
            <input type="number" value={energyConsumption.gas.toFixed(2)} readOnly />
          </label>
          <label>Вода (м³):
            <input type="number" value={energyConsumption.water.toFixed(2)} readOnly />
          </label>
        </div>
      </section>

      <section>
        <h2>Простой оборудования и инциденты</h2>
        <button onClick={handleAddDowntime}>Добавить простой</button>
        {downtime.map((item, idx) => (
          <div key={idx} className="downtime-row">
            <select value={item.type_of_problem} onChange={(e) => {
              const newDowntime = [...downtime];
              newDowntime[idx].type_of_problem = e.target.value;
              setDowntime(newDowntime);
            }}>
              <option value="">Выберите тип простоя</option>
              <option value="ремонт">Ремонт</option>
              <option value="авария">Авария</option>
              <option value="нехватка сырья">Нехватка сырья</option>
            </select>
            <input type="text" placeholder="Описание" value={item.problem} onChange={(e) => {
              const newDowntime = [...downtime];
              newDowntime[idx].problem = e.target.value;
              setDowntime(newDowntime);
            }} />
            <input type="time" value={item.problem_start} onChange={(e) => {
              const newDowntime = [...downtime];
              newDowntime[idx].problem_start = e.target.value;
              setDowntime(newDowntime);
            }} />
            <input type="time" value={item.problem_stop} onChange={(e) => {
              const newDowntime = [...downtime];
              newDowntime[idx].problem_stop = e.target.value;
              setDowntime(newDowntime);
            }} />
          </div>
        ))}
      </section>

      <section>
        <h2>Показатели качества</h2>
        <label>Твердость (МПа):
          <input type="number" value={quality.rav} readOnly />
        </label>
        <label>Плотность (кг/м³):
          <input type="number" value={quality.density} readOnly />
        </label>
        <label>Влажность (%):
          <input type="number" value={quality.humidity} readOnly />
        </label>
      </section>

      <section>
        <h2>Явка сотрудников по сменам</h2>
        {attendanceByShift.map((shift, shiftIndex) => (
          <div key={shiftIndex}>
            <h4>Смена: {shift.shift_name}</h4>
            <table>
              <thead>
                <tr>
                  <th>ФИО</th>
                  <th>Явка</th>
                  <th>Опоздание</th>
                  <th>Нарушения</th>
                </tr>
              </thead>
              <tbody>
                {shift.employees.map((emp, empIndex) => (
                  <tr key={empIndex}>
                    <td>{emp.name}</td>
                    <td>
                      <input
                        type="checkbox"
                        checked={emp.present}
                        onChange={(e) => {
                          const newAttendance = [...attendanceByShift];
                          newAttendance[shiftIndex].employees[empIndex].present = e.target.checked;
                          setAttendanceByShift(newAttendance);
                        }}
                      />
                    </td>
                    <td>
                      <input
                        type="text"
                        value={emp.late}
                        onChange={(e) => {
                          const newAttendance = [...attendanceByShift];
                          newAttendance[shiftIndex].employees[empIndex].late = e.target.value;
                          setAttendanceByShift(newAttendance);
                        }}
                      />
                    </td>
                    <td>
                      <input
                        type="text"
                        value={emp.violations}
                        onChange={(e) => {
                          const newAttendance = [...attendanceByShift];
                          newAttendance[shiftIndex].employees[empIndex].violations = e.target.value;
                          setAttendanceByShift(newAttendance);
                        }}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))}
      </section>

      <button onClick={handleSaveReport}>Сохранить отчет</button>
    </div>
  );
}

export default ReportScreen;