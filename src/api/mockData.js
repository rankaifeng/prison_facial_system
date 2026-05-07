// Mock Data Generation for Prison System

const FIRST_NAMES = ['张', '王', '李', '赵', '刘', '陈', '杨', '黄', '吴', '周', '徐', '孙', '马', '朱', '林', '郭', '何', '高', '罗', '郑'];
const LAST_NAMES = ['三', '五', '二', '四', '六', '七', '八', '九', '十', '明', '强', '伟', '华', '军', '平', '涛', '祥', '超', '龙', '飞'];
const CRIMES = ['盗窃罪', '抢劫罪', '诈骗罪', '故意伤害罪', '贩毒罪', '洗钱罪', '非法拘禁罪', '强奸罪', '杀人罪', '放火罪', '贪污罪', '受贿罪'];
const ADDRESSES = ['北京市朝阳区', '上海市浦东新区', '广州市越秀区', '深圳市南山区', '杭州市西湖区', '南京市鼓楼区', '武汉市武昌区', '西安市碑林区', '成都市锦江区', '重庆市渝中区'];
const PRISONS = [
  { id: 'P001', name: '第一监狱', city: '北京' },
  { id: 'P002', name: '第二监狱', city: '上海' },
  { id: 'P003', name: '第三监狱', city: '广州' },
  { id: 'P004', name: '第四监狱', city: '深圳' },
  { id: 'P005', name: '第五监狱', city: '杭州' },
  { id: 'P006', name: '第六监狱', city: '南京' },
  { id: 'P007', name: '第七监狱', city: '武汉' }
];
const STATUSES = ['在监', '出工', '住院', '禁闭', '隔离', '探亲', '惩戒'];
const EXIT_REASONS = ['刑期满释放', '减刑释放', '假释', '特赦', '因病释放', '死亡', '逃脱', '保外就医'];

const randomElement = (arr) => arr[Math.floor(Math.random() * arr.length)];
const randomInt = (min, max) => Math.floor(Math.random() * (max - min + 1)) + min;
const randomBool = () => Math.random() > 0.5;

const formatDate = (date) => {
  return date.toISOString().split('T')[0];
};

const formatDateTime = (date) => {
  return date.toISOString().replace('T', ' ').substring(0, 19);
};

// Generate Chinese name
const generateName = () => {
  return randomElement(FIRST_NAMES) + randomElement(LAST_NAMES);
};

// Generate ID Card Number
const generateIdCard = () => {
  const areas = ['110101', '310101', '440101', '440305', '330105', '320101', '420101', '610102', '510104', '500103'];
  const area = randomElement(areas);
  const year = randomInt(1960, 2000);
  const month = randomInt(1, 12).toString().padStart(2, '0');
  const day = randomInt(1, 28).toString().padStart(2, '0');
  const seq = randomInt(0, 999).toString().padStart(3, '0');
  const check = randomInt(0, 9);
  return `${area}${year}${month}${day}${seq}${check}`;
};

// Generate Prisoner Number
const generatePrisonerNo = (index) => {
  const prisonId = ['YJ', 'SH', 'GZ', 'SZ', 'HZ', 'NJ', 'WH'][index % 7];
  return `${prisonId}-${String(index + 1).padStart(4, '0')}`;
};

// Mock Data Generators

export const mockPrisons = () => {
  return PRISONS.map(prison => ({
    ...prison,
    totalCount: randomInt(300, 800),
    workCount: randomInt(50, 200),
    imageUrl: '/imgs/jy.png'
  }));
};

export const mockPrisoner = (index) => {
  const birthYear = randomInt(1960, 2000);
  const sentenceStartDate = new Date(randomInt(2015, 2022), randomInt(0, 11), randomInt(1, 28));
  const sentenceYears = randomInt(1, 20);
  const sentenceEndDate = new Date(sentenceStartDate.getFullYear() + sentenceYears, sentenceStartDate.getMonth(), sentenceStartDate.getDate());

  return {
    id: `PR${String(index + 1).padStart(6, '0')}`,
    name: generateName(),
    gender: randomElement(['男', '女']),
    age: new Date().getFullYear() - birthYear,
    ethnicity: randomElement(['汉族', '回族', '维吾尔族', '蒙古族', '满族']),
    birthplace: randomElement(ADDRESSES),
    maritalStatus: randomElement(['未婚', '已婚', '离异', '丧偶']),
    idCardType: '身份证',
    idCard: generateIdCard(),
    registeredAddress: randomElement(ADDRESSES),
    prisonerNo: generatePrisonerNo(index),
    crime: randomElement(CRIMES),
    sentence: `${sentenceYears}年`,
    incarcerationReason: randomElement(CRIMES),
    incarcerationDate: formatDate(sentenceStartDate),
    releaseDate: formatDate(sentenceEndDate),
    sentenceStart: formatDate(sentenceStartDate),
    sentenceEnd: formatDate(sentenceEndDate),
    entryDate: formatDate(sentenceStartDate),
    status: randomElement(STATUSES),
    photo: '/imgs/face.png',
    prisonId: randomElement(PRISONS.map(p => p.id))
  };
};

export const mockPrisoners = (count = 100) => {
  return Array.from({ length: count }, (_, i) => mockPrisoner(i));
};

export const mockExitRecord = (index, prisonerId) => {
  const exitDate = new Date();
  exitDate.setDate(exitDate.getDate() - randomInt(1, 365));
  const returnDate = new Date(exitDate);
  returnDate.setHours(returnDate.getHours() + randomInt(1, 12));

  return {
    id: `ER${String(index + 1).padStart(6, '0')}`,
    exitTime: formatDateTime(exitDate),
    exitDate: formatDate(exitDate),
    exitReason: randomElement(EXIT_REASONS),
    hospital: randomElement(['北京市第一医院', '上海市医院', '广州市医院', '深圳市医院', '杭州市医院']),
    policeConfirm: randomBool(),
    swatConfirm: randomBool(),
    armedPoliceConfirm: randomBool(),
    returnTime: formatDateTime(returnDate),
    videoRecord: randomBool(),
    prisonerName: generateName(),
    prisonerNo: generatePrisonerNo(index),
    prisonId: randomElement(PRISONS.map(p => p.id)),
    prisonerDetail: prisonerId
  };
};

export const mockExitRecordsForPrisoner = (prisonerId, count = 20) => {
  return Array.from({ length: count }, (_, i) => mockExitRecord(i, prisonerId));
};

export const mockExitRecords = (count = 50) => {
  return Array.from({ length: count }, (_, i) => mockExitRecord(i, `PR${String(i + 1).padStart(6, '0')}`));
};

export const mockRealtimeStatistics = () => {
  const total = randomInt(700, 1000);
  const inPrison = Math.floor(total * 0.84);
  const working = Math.floor(total * 0.08);
  const hospital = Math.floor(total * 0.02);
  const isolated = Math.floor(total * 0.02);
  const quarantine = Math.floor(total * 0.01);
  const visiting = Math.floor(total * 0.02);
  const punishment = total - inPrison - working - hospital - isolated - quarantine - visiting;

  return {
    total,
    normalPercentage: 84,
    stats: {
      inPrison,
      working,
      hospital,
      isolated,
      quarantine,
      visiting,
      punishment
    }
  };
};

export const mockWorkStatistics = () => {
  const months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12'];
  return months.map(month => ({
    month,
    prisons: PRISONS.map(prison => ({
      name: prison.name,
      value: randomInt(50, 200)
    }))
  }));
};

export const mockExitStatistics = (count = 50) => {
  return Array.from({ length: count }, (_, i) => {
    const exitDate = new Date();
    exitDate.setDate(exitDate.getDate() - randomInt(1, 90));
    return {
      id: `ES${String(i + 1).padStart(6, '0')}`,
      prisonName: randomElement(PRISONS.map(p => p.name)),
      prisonerName: generateName(),
      prisonerNo: generatePrisonerNo(i),
      exitTime: formatDateTime(exitDate),
      exitReason: randomElement(EXIT_REASONS),
      hospital: randomBool(),
      policeConfirm: randomBool(),
      swatConfirm: randomBool(),
      armedPoliceConfirm: randomBool(),
      returnTime: formatDateTime(new Date(exitDate.getTime() + randomInt(1, 12) * 3600000)),
      videoRecord: randomBool()
    };
  });
};

export const mockMessage = (index) => {
  const actions = ['进监', '出狱', '越狱', '打架', '自伤', '死亡', '突发状况'];
  const actionIndex = randomInt(0, actions.length - 1);
  const now = new Date();
  const msgTime = new Date(now.getTime() - randomInt(1, 3600000 * 24));

  return {
    id: `MSG${String(index + 1).padStart(6, '0')}`,
    prisonName: randomElement(PRISONS.map(p => p.name)),
    personName: generateName(),
    action: actions[actionIndex],
    time: formatDateTime(msgTime),
    detail: `${randomElement(PRISONS.map(p => p.name))} - ${generateName()} - ${actions[actionIndex]}`
  };
};

export const mockMessages = (count = 10) => {
  return Array.from({ length: count }, (_, i) => mockMessage(i));
};

export const mockAccount = (index, role = 'operator') => {
  const roles = ['admin', 'operator', 'manager'];
  const role_names = ['管理员', '操作员', '经理'];
  const selectedRole = role || randomElement(roles);
  const roleIndex = roles.indexOf(selectedRole);

  return {
    id: `ACC${String(index + 1).padStart(6, '0')}`,
    username: `user${index + 1}`,
    name: generateName(),
    role: selectedRole,
    roleName: role_names[roleIndex],
    prison: randomElement(PRISONS.map(p => p.name)),
    password: 'encrypted_password_' + index,
    status: 'active',
    createdAt: formatDate(new Date(Date.now() - randomInt(1, 365 * 24 * 3600000)))
  };
};

export const mockAccounts = (count = 20) => {
  const accounts = [];
  accounts.push(mockAccount(0, 'admin'));
  accounts.push(mockAccount(1, 'manager'));

  for (let i = 2; i < count; i++) {
    accounts.push(mockAccount(i, 'operator'));
  }

  return accounts;
};

export const mockPrisonerArchive = (count = 50) => {
  return Array.from({ length: count }, (_, i) => ({
    id: `PA${String(i + 1).padStart(6, '0')}`,
    prisonerNo: generatePrisonerNo(i),
    name: generateName(),
    crime: randomElement(CRIMES),
    sentence: `${randomInt(1, 20)}年`,
    entryDate: formatDate(new Date(Date.now() - randomInt(1, 365 * 24 * 3600000))),
    releaseDate: formatDate(new Date(Date.now() + randomInt(1, 365 * 24 * 3600000))),
    status: randomElement(STATUSES),
    prisonId: randomElement(PRISONS.map(p => p.id))
  }));
};

// API Response Wrapper
export const mockResponse = (data, total = null) => {
  return {
    code: 200,
    message: 'success',
    data: data,
    total: total || (Array.isArray(data) ? data.length : 1)
  };
};

export const mockListResponse = (data, page = 1, pageSize = 10) => {
  const total = data.length;
  const startIndex = (page - 1) * pageSize;
  const paginatedData = data.slice(startIndex, startIndex + pageSize);

  return {
    code: 200,
    message: 'success',
    data: paginatedData,
    total: total,
    page: page,
    pageSize: pageSize,
    pageCount: Math.ceil(total / pageSize)
  };
};
