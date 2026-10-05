-- =============================================================================
-- 适老化社区养老智能助手 — 数据库全量脚本（唯一入口）
-- 导入：在项目根目录用数据库客户端导入本脚本，字符集选四字节统一编码
-- 说明：会创建并选用养老库，删除业务表后重建并写入种子数据
-- =============================================================================

CREATE DATABASE IF NOT EXISTS elder_care DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE elder_care;

-- -----------------------------------------------------------------------------
-- 表结构
-- -----------------------------------------------------------------------------

DROP TABLE IF EXISTS agent_tool_call_log;
DROP TABLE IF EXISTS agent_conversation;
DROP TABLE IF EXISTS notify_inbox;
DROP TABLE IF EXISTS medication_log;
DROP TABLE IF EXISTS medication_schedule;
DROP TABLE IF EXISTS service_booking;
DROP TABLE IF EXISTS service_catalog;
DROP TABLE IF EXISTS activity_registration;
DROP TABLE IF EXISTS community_activity;
DROP TABLE IF EXISTS emergency_alert;
DROP TABLE IF EXISTS knowledge_chunk;
DROP TABLE IF EXISTS knowledge_document;
DROP TABLE IF EXISTS family_member;
DROP TABLE IF EXISTS elder_profile;
DROP TABLE IF EXISTS sys_operation_log;
DROP TABLE IF EXISTS sys_login_log;
DROP TABLE IF EXISTS sys_menu;
DROP TABLE IF EXISTS sys_user;
DROP TABLE IF EXISTS sys_role;

CREATE TABLE sys_role (
    id          BIGINT       NOT NULL AUTO_INCREMENT,
    code        VARCHAR(30)  NOT NULL COMMENT '角色编码',
    name        VARCHAR(50)  NOT NULL COMMENT '角色名称',
    sort_order  INT          NOT NULL DEFAULT 0 COMMENT '排序',
    status      TINYINT      NOT NULL DEFAULT 1 COMMENT '0禁用 1启用',
    PRIMARY KEY (id),
    UNIQUE KEY uk_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色表';

CREATE TABLE sys_user (
    id          BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键',
    username    VARCHAR(50)  NOT NULL COMMENT '用户名',
    password    VARCHAR(100) NOT NULL COMMENT '密码（加密哈希）',
    nickname    VARCHAR(50)  DEFAULT NULL COMMENT '昵称',
    email       VARCHAR(100) DEFAULT NULL COMMENT '邮箱',
    phone       VARCHAR(20)  DEFAULT NULL COMMENT '手机号',
    avatar      VARCHAR(255) DEFAULT NULL COMMENT '头像访问路径，如上传目录下的图片文件',
    status      TINYINT      NOT NULL DEFAULT 1 COMMENT '状态：0禁用 1启用',
    role        VARCHAR(30)  NOT NULL DEFAULT 'USER' COMMENT '角色编码，对应角色表编码',
    create_time DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

CREATE TABLE sys_menu (
    id          BIGINT       NOT NULL AUTO_INCREMENT,
    parent_id   BIGINT       NOT NULL DEFAULT 0 COMMENT '父菜单，0为顶级',
    name        VARCHAR(50)  NOT NULL COMMENT '菜单名称',
    path        VARCHAR(100) NOT NULL COMMENT '前端路由',
    icon        VARCHAR(50)  DEFAULT NULL COMMENT '图标名（前端图标组件）',
    sort_order  INT          NOT NULL DEFAULT 0 COMMENT '排序',
    roles       VARCHAR(100) NOT NULL DEFAULT 'ADMIN' COMMENT '固定为管理员角色（仅后台菜单）',
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='菜单表';

CREATE TABLE sys_login_log (
    id          BIGINT       NOT NULL AUTO_INCREMENT,
    username    VARCHAR(50)  NOT NULL COMMENT '登录账号',
    ip          VARCHAR(50)  DEFAULT NULL COMMENT '登录网络地址',
    status      TINYINT      NOT NULL COMMENT '0失败 1成功',
    message     VARCHAR(200) DEFAULT NULL COMMENT '说明',
    create_time DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_create_time (create_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='登录日志';

CREATE TABLE sys_operation_log (
    id          BIGINT       NOT NULL AUTO_INCREMENT,
    username    VARCHAR(50)  DEFAULT NULL COMMENT '操作人',
    module      VARCHAR(50)  DEFAULT NULL COMMENT '模块',
    action      VARCHAR(50)  DEFAULT NULL COMMENT '操作',
    method      VARCHAR(10)  DEFAULT NULL COMMENT '请求方式',
    url         VARCHAR(200) DEFAULT NULL COMMENT '请求地址',
    ip          VARCHAR(50)  DEFAULT NULL COMMENT '请求网络地址',
    cost_ms     INT          DEFAULT NULL COMMENT '耗时毫秒',
    status      TINYINT      NOT NULL DEFAULT 1 COMMENT '0失败 1成功',
    create_time DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_create_time (create_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='操作日志';

-- -----------------------------------------------------------------------------
-- 业务表：社区养老核心业务
-- -----------------------------------------------------------------------------

CREATE TABLE elder_profile (
    id                   BIGINT       NOT NULL AUTO_INCREMENT,
    name                 VARCHAR(50)  NOT NULL COMMENT '姓名',
    gender               TINYINT      DEFAULT NULL COMMENT '0女 1男',
    birth_date           DATE         DEFAULT NULL,
    phone                VARCHAR(20)  DEFAULT NULL,
    address              VARCHAR(200) DEFAULT NULL,
    emergency_contact    VARCHAR(50)  DEFAULT NULL,
    emergency_phone      VARCHAR(20)  DEFAULT NULL,
    chronic_diseases     TEXT         DEFAULT NULL COMMENT '慢性病',
    current_medications  TEXT         DEFAULT NULL COMMENT '当前用药摘要',
    health_summary       TEXT         DEFAULT NULL,
    status               TINYINT      NOT NULL DEFAULT 1 COMMENT '1正常 0停用',
    create_time          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_time          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_elder_name (name),
    KEY idx_elder_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='老人档案';

CREATE TABLE family_member (
    id          BIGINT       NOT NULL AUTO_INCREMENT,
    user_id     BIGINT       NOT NULL COMMENT '用户表主键',
    elder_id    BIGINT       NOT NULL COMMENT '老人档案主键',
    relation    VARCHAR(20)  DEFAULT NULL COMMENT '子女/配偶等',
    is_primary  TINYINT      NOT NULL DEFAULT 0,
    create_time DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_user_elder (user_id, elder_id),
    UNIQUE KEY uk_family_elder (elder_id) COMMENT '每位老人仅一位家属'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='家属绑定';

CREATE TABLE medication_schedule (
    id             BIGINT       NOT NULL AUTO_INCREMENT,
    elder_id       BIGINT       NOT NULL,
    drug_name      VARCHAR(100) NOT NULL,
    dosage         VARCHAR(50)  DEFAULT NULL,
    schedule_times VARCHAR(100) NOT NULL COMMENT '如 08:00,20:00',
    start_date     DATE         DEFAULT NULL,
    end_date       DATE         DEFAULT NULL,
    remark         VARCHAR(200) DEFAULT NULL,
    status         TINYINT      NOT NULL DEFAULT 1,
    create_time    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_time    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_med_sched_elder (elder_id, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用药计划';

CREATE TABLE medication_log (
    id           BIGINT   NOT NULL AUTO_INCREMENT,
    schedule_id  BIGINT   NOT NULL,
    elder_id     BIGINT   NOT NULL,
    planned_time DATETIME NOT NULL,
    taken_time   DATETIME DEFAULT NULL,
    status       TINYINT  NOT NULL DEFAULT 2 COMMENT '1已服 0漏服 2待服',
    create_time  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_med_log_elder_time (elder_id, planned_time),
    KEY idx_med_log_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用药执行记录';

CREATE TABLE service_catalog (
    id                BIGINT       NOT NULL AUTO_INCREMENT,
    name              VARCHAR(100) NOT NULL,
    service_type      VARCHAR(50)  NOT NULL COMMENT '服务类型：体检/护理/家政',
    description       TEXT         DEFAULT NULL,
    duration_minutes  INT          DEFAULT 60,
    status            TINYINT      NOT NULL DEFAULT 1,
    create_time       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_time       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_catalog_type (service_type, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='服务目录';

CREATE TABLE service_booking (
    id           BIGINT       NOT NULL AUTO_INCREMENT,
    elder_id     BIGINT       NOT NULL,
    catalog_id   BIGINT       NOT NULL,
    booking_time DATETIME     NOT NULL,
    status       VARCHAR(20)  NOT NULL DEFAULT 'pending' COMMENT '待确认/已确认/已取消/已完成',
    source       VARCHAR(20)  NOT NULL DEFAULT 'manual' COMMENT '人工/智能助手',
    remark       VARCHAR(200) DEFAULT NULL,
    slot_lock    VARCHAR(64)  DEFAULT NULL COMMENT '有效预约时段锁键；取消/完成后置空',
    version      INT          NOT NULL DEFAULT 0 COMMENT '乐观锁版本号',
    create_time  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_time  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_booking_slot_lock (slot_lock),
    KEY idx_booking_elder (elder_id, booking_time),
    KEY idx_booking_slot (catalog_id, booking_time, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='服务预约';

CREATE TABLE agent_conversation (
    id          BIGINT       NOT NULL AUTO_INCREMENT,
    user_id     BIGINT       NOT NULL,
    elder_id    BIGINT       DEFAULT NULL,
    session_id  VARCHAR(64)  NOT NULL,
    role        VARCHAR(20)  NOT NULL COMMENT '用户/助手/系统',
    content     TEXT         NOT NULL,
    create_time DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_agent_session (session_id, create_time),
    KEY idx_agent_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='智能助手对话';

CREATE TABLE agent_tool_call_log (
    id               BIGINT       NOT NULL AUTO_INCREMENT,
    session_id       VARCHAR(64)  NOT NULL,
    conversation_id  BIGINT       DEFAULT NULL,
    user_id          BIGINT       NOT NULL,
    tool_name        VARCHAR(64)  NOT NULL,
    request_args     TEXT         DEFAULT NULL,
    response_data    TEXT         DEFAULT NULL,
    status           TINYINT      NOT NULL DEFAULT 1 COMMENT '1成功 0失败',
    cost_ms          INT          DEFAULT NULL,
    create_time      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_tool_log_session (session_id),
    KEY idx_tool_log_name (tool_name, create_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='智能助手工具调用日志';

CREATE TABLE community_activity (
    id          BIGINT       NOT NULL AUTO_INCREMENT,
    title       VARCHAR(100) NOT NULL,
    content     TEXT         DEFAULT NULL,
    location    VARCHAR(200) DEFAULT NULL,
    start_time  DATETIME     NOT NULL,
    end_time    DATETIME     DEFAULT NULL,
    capacity    INT          DEFAULT NULL COMMENT '名额，空不限',
    status      TINYINT      NOT NULL DEFAULT 1 COMMENT '1报名中 0下架',
    create_time DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_activity_status (status, start_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='社区活动';

CREATE TABLE activity_registration (
    id          BIGINT       NOT NULL AUTO_INCREMENT,
    activity_id BIGINT       NOT NULL,
    elder_id    BIGINT       NOT NULL,
    user_id     BIGINT       DEFAULT NULL COMMENT '代报名子女',
    status      VARCHAR(20)  NOT NULL DEFAULT 'registered' COMMENT '已报名/已取消',
    create_time DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_activity_elder (activity_id, elder_id),
    KEY idx_reg_elder (elder_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='活动报名';

CREATE TABLE emergency_alert (
    id            BIGINT       NOT NULL AUTO_INCREMENT,
    elder_id      BIGINT       NOT NULL,
    location      VARCHAR(200) DEFAULT NULL,
    message       TEXT         DEFAULT NULL,
    status        VARCHAR(20)  NOT NULL DEFAULT 'open' COMMENT '待处理/处理中/已关闭',
    notify_family TINYINT      NOT NULL DEFAULT 0,
    notify_staff  TINYINT      NOT NULL DEFAULT 0,
    source        VARCHAR(20)  NOT NULL DEFAULT 'manual' COMMENT '人工/智能助手',
    create_time   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_time   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_alert_elder (elder_id, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='紧急呼叫';

CREATE TABLE notify_inbox (
    id          BIGINT       NOT NULL AUTO_INCREMENT,
    user_id     BIGINT       NOT NULL COMMENT '接收人用户主键',
    elder_id    BIGINT       DEFAULT NULL COMMENT '关联老人',
    title       VARCHAR(100) NOT NULL,
    content     TEXT         NOT NULL,
    msg_type    VARCHAR(30)  NOT NULL DEFAULT 'system' COMMENT '助手通知/用药/预约/紧急/系统',
    source      VARCHAR(20)  NOT NULL DEFAULT 'system' COMMENT '助手/系统/人工',
    related_id  BIGINT       DEFAULT NULL,
    is_read     TINYINT      NOT NULL DEFAULT 0 COMMENT '0未读 1已读',
    create_time DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_inbox_user_read (user_id, is_read, id),
    KEY idx_inbox_elder (elder_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='站内消息收件箱';

CREATE TABLE knowledge_document (
    id          BIGINT       NOT NULL AUTO_INCREMENT,
    title       VARCHAR(200) NOT NULL,
    file_path   VARCHAR(500) DEFAULT NULL,
    doc_type    VARCHAR(50)  DEFAULT NULL COMMENT '政策/用药/服务',
    status      TINYINT      NOT NULL DEFAULT 0 COMMENT '0待向量化 1已就绪',
    create_time DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识库文档';

CREATE TABLE knowledge_chunk (
    id           BIGINT       NOT NULL AUTO_INCREMENT,
    document_id  BIGINT       NOT NULL,
    chunk_index  INT          NOT NULL,
    content      TEXT         NOT NULL,
    embedding_id VARCHAR(100) DEFAULT NULL COMMENT '向量库中的标识',
    create_time  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_chunk_doc (document_id, chunk_index)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识切片';

-- -----------------------------------------------------------------------------
-- 初始数据：角色（用户表角色字段存编码，一人一角）
-- 扩展：向角色表插入新角色后，在前端路由权限与后台鉴权中配置对应编码（菜单表仅后台管理员）
-- -----------------------------------------------------------------------------

INSERT INTO sys_role (code, name, sort_order, status) VALUES
('ADMIN', '管理员', 1, 1),
('USER',  '用户',   2, 1);

-- -----------------------------------------------------------------------------
-- 初始数据：用户（密码分别为管理员口令与普通用户口令，已加密存储）
-- -----------------------------------------------------------------------------

INSERT INTO sys_user (username, password, nickname, email, phone, status, role) VALUES
('admin', '$2a$10$B4MRmEk2dlZGVJpSjYYlduf2mJA3VbiaZXECIv4gHVdhBWprShqEm', '系统管理员', 'admin@system.com', '13800000001', 1, 'ADMIN'),
('aaa',   '$2a$10$dskSVl8JS.wg923Vre3gy.XxM/fh3c0.OoIoETv85PQsJRuaLq30C', '用户A',      'aaa@system.com',   '13800000002', 1, 'USER'),
('bbb',   '$2a$10$dskSVl8JS.wg923Vre3gy.XxM/fh3c0.OoIoETv85PQsJRuaLq30C', '用户B',      'bbb@system.com',   '13800000003', 1, 'USER'),
('ccc',   '$2a$10$dskSVl8JS.wg923Vre3gy.XxM/fh3c0.OoIoETv85PQsJRuaLq30C', '王强',        'ccc@system.com',   '13800000004', 1, 'USER'),
('ddd',   '$2a$10$dskSVl8JS.wg923Vre3gy.XxM/fh3c0.OoIoETv85PQsJRuaLq30C', '赵丽',        'ddd@system.com',   '13800000005', 1, 'USER'),
('eee',   '$2a$10$dskSVl8JS.wg923Vre3gy.XxM/fh3c0.OoIoETv85PQsJRuaLq30C', '陈伟',        'eee@system.com',   '13800000006', 1, 'USER'),
('fff',   '$2a$10$dskSVl8JS.wg923Vre3gy.XxM/fh3c0.OoIoETv85PQsJRuaLq30C', '刘敏',        'fff@system.com',   '13800000007', 1, 'USER'),
('ggg',   '$2a$10$dskSVl8JS.wg923Vre3gy.XxM/fh3c0.OoIoETv85PQsJRuaLq30C', '孙杰',        'ggg@system.com',   '13800000008', 1, 'USER');

-- -----------------------------------------------------------------------------
-- 初始数据：后台菜单（仅管理端路径；用户前台路由写死在前端，不入库）
-- -----------------------------------------------------------------------------

INSERT INTO sys_menu (parent_id, name, path, icon, sort_order, roles) VALUES
(0, '数据概览', '/admin/dashboard',    'HomeFilled', 1,  'ADMIN'),
(0, '老人档案', '/admin/elders',       'Avatar',     2,  'ADMIN'),
(0, '用药管理', '/admin/medications',  'Postcard',   3, 'ADMIN'),
(0, '服务预约', '/admin/bookings',     'Calendar',   4,  'ADMIN'),
(0, '社区活动', '/admin/activities',   'Trophy',     5,  'ADMIN'),
(0, '紧急告警', '/admin/alerts',       'Bell',       6,  'ADMIN'),
(0, '知识库',   '/admin/knowledge',    'Reading',    7,  'ADMIN'),
(0, 'Agent工具', '/admin/agent-tools', 'SetUp',      8,  'ADMIN'),
(0, 'Agent日志', '/admin/agent-logs',  'Cpu',        9,  'ADMIN'),
(0, '用户管理', '/admin/users',        'User',       10, 'ADMIN'),
(0, '系统日志', '/admin/logs',         'Document',   11, 'ADMIN'),
(0, '菜单管理', '/admin/menus',        'Menu',       12, 'ADMIN');

-- -----------------------------------------------------------------------------
-- 业务种子：演示「漏服药 + 约体检」及更多档案
-- 用户甲→张建国；用户乙→李秀英；用户丙→王德福；用户丁→赵桂兰；用户戊→陈志国；用户己→刘玉珍；用户庚→孙永年
-- -----------------------------------------------------------------------------

INSERT INTO elder_profile (
    name, gender, birth_date, phone, address,
    emergency_contact, emergency_phone,
    chronic_diseases, current_medications, health_summary, status
) VALUES
('张建国', 1, '1952-03-15', '13900001111', '阳光社区 3 栋 201',
 '张明（儿子）', '13800000002',
 '高血压,轻度骨质疏松', '氨氯地平 5mg 早8点/晚8点',
 '血压偏高，需规律服药；近一周偶有头晕。', 1),
('李秀英', 0, '1948-11-02', '13900002222', '阳光社区 5 栋 502',
 '李芳（女儿）', '13800000003',
 '2型糖尿病', '二甲双胍 0.5g 餐后',
 '血糖控制尚可，注意饮食。', 1),
('王德福', 1, '1950-06-20', '13900003333', '阳光社区 2 栋 105',
 '王强（儿子）', '13800000004',
 '冠心病,高血脂', '阿托伐他汀 20mg 晚间',
 '近期胸闷减轻，需继续低盐低脂饮食。', 1),
('赵桂兰', 0, '1949-09-12', '13900004444', '阳光社区 6 栋 301',
 '赵丽（女儿）', '13800000005',
 '骨质疏松,轻度贫血', '钙尔奇 D 每日1片',
 '行动尚可，上下楼需搀扶，防跌倒。', 1),
('陈志国', 1, '1955-01-08', '13900005555', '阳光社区 1 栋 402',
 '陈伟（儿子）', '13800000006',
 '高血压,慢性支气管炎', '缬沙坦 80mg 晨服',
 '冬季易咳喘，注意保暖与按时服药。', 1),
('刘玉珍', 0, '1947-04-25', '13900006666', '阳光社区 8 栋 601',
 '刘敏（女儿）', '13800000007',
 '2型糖尿病,白内障术后', '格列美脲 2mg 早餐前',
 '血糖总体平稳，视力恢复中，避免剧烈运动。', 1),
('孙永年', 1, '1945-12-03', '13900007777', '阳光社区 4 栋 203',
 '孙杰（孙子）', '13800000008',
 '帕金森病早期,便秘', '美多芭 按医嘱分次',
 '手抖轻微，需督促按时服药与适量活动。', 1);

INSERT INTO family_member (user_id, elder_id, relation, is_primary) VALUES
(2, 1, '儿子', 1),
(3, 2, '女儿', 1),
(4, 3, '儿子', 1),
(5, 4, '女儿', 1),
(6, 5, '儿子', 1),
(7, 6, '女儿', 1),
(8, 7, '孙子', 1);

INSERT INTO notify_inbox (user_id, elder_id, title, content, msg_type, source, is_read) VALUES
(2, 1, '用药提醒：发现漏服',
 '智能助手检测到张建国近几日有降压药漏服记录，请督促按时服药，或在「服药打卡」中标记已服。',
 'medication', 'system', 0),
(3, 2, '健康关怀提醒',
 '李秀英的用药计划已同步，如有漏服或异常，智能助手会向您发送站内消息。',
 'system', 'system', 0);

INSERT INTO medication_schedule (
    elder_id, drug_name, dosage, schedule_times, start_date, remark, status
) VALUES
(1, '氨氯地平', '5mg', '08:00,20:00', '2026-01-01', '降压药，勿漏服', 1),
(2, '二甲双胍', '0.5g', '08:30,18:30', '2026-01-01', '餐后服用', 1),
(3, '阿托伐他汀', '20mg', '20:00', '2026-01-01', '降脂，晚间服用', 1),
(4, '钙尔奇D', '1片', '08:00', '2026-01-01', '补钙', 1),
(5, '缬沙坦', '80mg', '08:00', '2026-01-01', '降压药', 1),
(6, '格列美脲', '2mg', '07:30', '2026-01-01', '降糖，早餐前', 1),
(7, '美多芭', '按医嘱', '08:00,14:00,20:00', '2026-01-01', '帕金森用药', 1);

INSERT INTO medication_log (schedule_id, elder_id, planned_time, taken_time, status) VALUES
(1, 1, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 4 DAY), '08:00:00'), TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 4 DAY), '08:12:00'), 1),
(1, 1, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 4 DAY), '20:00:00'), NULL, 0),
(1, 1, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 3 DAY), '08:00:00'), NULL, 0),
(1, 1, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 3 DAY), '20:00:00'), TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 3 DAY), '20:05:00'), 1),
(1, 1, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 2 DAY), '08:00:00'), NULL, 0),
(1, 1, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 2 DAY), '20:00:00'), TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 2 DAY), '20:10:00'), 1),
(1, 1, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 1 DAY), '08:00:00'), NULL, 0),
(1, 1, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 1 DAY), '20:00:00'), NULL, 0),
(1, 1, TIMESTAMP(CURDATE(), '08:00:00'), NULL, 0),
(2, 2, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 2 DAY), '08:30:00'), NULL, 0),
(2, 2, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 1 DAY), '08:30:00'), TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 1 DAY), '08:40:00'), 1);

INSERT INTO service_catalog (name, service_type, description, duration_minutes, status) VALUES
('社区体检', 'health_check', '常规体检：血压、血糖、心电图等', 60, 1),
('上门护理', 'nursing', '护士上门测血压、用药指导', 45, 1),
('家政保洁', 'housekeeping', '居家清洁与整理', 120, 1);

INSERT INTO community_activity (title, content, location, start_time, end_time, capacity, status) VALUES
('晨练太极班', '适合中轻度活动能力的长辈，社区教练带练。', '阳光社区广场', '2026-07-25 07:30:00', '2026-07-25 08:30:00', 30, 1),
('书画兴趣小组', '宣纸毛笔自备，茶歇免费。', '社区活动室 A', '2026-07-26 14:00:00', '2026-07-26 16:00:00', 20, 1),
('健康讲座：血压管理', '社区医生讲解降压药与日常监测要点。', '社区礼堂', '2026-07-28 09:30:00', '2026-07-28 11:00:00', 50, 1);

-- 知识库种子（切片内容入库；首次查询或启动时会同步写入向量库）
INSERT INTO knowledge_document (title, file_path, doc_type, status) VALUES
('社区居家养老服务补贴指引', 'seed/policy_subsidy.txt', 'policy', 1),
('老年人降压药日常注意事项', 'seed/medication_bp.txt', 'medication', 1),
('社区助餐服务办理指南', 'seed/service_meal.txt', 'service', 1),
('上门护理服务内容与预约须知', 'seed/service_nursing.txt', 'service', 1),
('糖尿病老人用药与饮食建议', 'seed/medication_diabetes.txt', 'medication', 1),
('居家防跌倒安全要点', 'seed/policy_fall_prevention.txt', 'policy', 1),
('社区体检预约与报告解读', 'seed/service_checkup.txt', 'service', 1),
('认知障碍老人家属陪伴指南', 'seed/policy_dementia_care.txt', 'policy', 1),
('老年人感冒药使用提醒', 'seed/medication_cold.txt', 'medication', 1);

INSERT INTO knowledge_chunk (document_id, chunk_index, content, embedding_id) VALUES
(1, 0, '阳光社区为户籍且年满60周岁的居家老年人提供养老服务补贴。补贴可用于上门护理、助餐、助洁等社区服务，不可兑换现金。申请需携带身份证与户口本到社区服务站登记，审核通过后次月生效。', 'seed-1-0'),
(1, 1, '补贴标准按身体能力评估分为三档：能力完好每月200元，轻度失能每月400元，中重度失能每月600元。同一老人不可同时享受机构托养全额补贴与居家补贴。如有疑问可拨打社区养老热线400-800-5678。', 'seed-1-1'),
(1, 2, '补贴账户按月充值至社区养老服务卡，可在签约服务商处刷卡消费。未使用余额可累计至当年12月31日，逾期清零。更换住址需在15日内到新社区办理迁移，否则暂停发放。', 'seed-1-2'),
(2, 0, '降压药（如氨氯地平、缬沙坦等）应遵医嘱定时定量服用，不可因血压暂时正常而自行停药。漏服时：若接近下次服药时间则跳过漏服剂量，切勿一次服用双倍剂量。服药期间避免突然起立，以防体位性低血压导致跌倒。', 'seed-2-0'),
(2, 1, '建议家属协助设置早晚服药闹钟，并将药品放在显眼位置。若出现持续头晕、胸闷、水肿加重，应及时联系社区医生或前往医院复诊，不要自行更换药品品牌与剂量。', 'seed-2-1'),
(2, 2, '日常监测：建议早晨起床后、服药前测量血压并记录；收缩压持续高于150mmHg或低于90mmHg，或伴有视物模糊、剧烈头痛时，应尽快就医。服药期间少吃过咸食物，适量散步，避免空腹大量饮酒。', 'seed-2-2'),
(3, 0, '阳光社区助餐点每日提供午餐，开放时间为11:00—13:00。户籍老人凭养老服务卡或身份证登记后就餐，能力完好者每餐自付8元，轻度及以上失能者可使用补贴抵扣部分费用。', 'seed-3-0'),
(3, 1, '助餐菜品兼顾低盐低脂，每周公布食谱。有糖尿病、痛风等特殊饮食需求的老人，可提前向助餐点登记，尽量提供替代餐。不能到点就餐的，可预约上门送餐，半径3公里内每单加收2元配送费。', 'seed-3-1'),
(3, 2, '春节、中秋等节假日助餐点照常开放，但需提前一天预约。如遇极端天气临时停餐，社区将通过电话或微信群通知家属。投诉与建议可拨打社区养老热线。', 'seed-3-2'),
(4, 0, '社区上门护理服务包括：测血压血糖、协助服药、基础伤口换药、生活照料指导等。护理人员均为持证护士或经过培训的护理员，每次服务前会核对照片与工牌。', 'seed-4-0'),
(4, 1, '预约方式：子女可通过社区养老助手或服务中心电话预约，也可由智能助手代为预约。一般需提前1个工作日预约，紧急情况可申请当日加急（视排班而定）。', 'seed-4-1'),
(4, 2, '服务过程中如老人出现不适，护理员将立即停止操作并联系家属与社区医生。服务结束后家属可在系统中评价。请勿私下向护理员额外付费或索要药品。', 'seed-4-2'),
(5, 0, '老年糖尿病患者应遵医嘱按时服用降糖药或注射胰岛素，不可因餐后血糖暂时正常而自行减量。漏服口服药时，若距下次服药超过2小时可补服一次常规剂量，接近下次服药则跳过，切勿加倍。', 'seed-5-0'),
(5, 1, '饮食上宜定时定量，主食粗细搭配，控制甜食与含糖饮料；可少量多餐。出现心慌、出冷汗、手抖等低血糖症状时，立即吃几块糖或喝半杯糖水，并监测血糖，必要时就医。', 'seed-5-1'),
(5, 2, '家属应协助记录血糖本（空腹、餐后2小时），复诊时带给医生。合并高血压者需同时管理血压与血脂。足部每日检查有无破损，穿宽松鞋袜，避免自行修剪过深老茧。', 'seed-5-2'),
(6, 0, '居家防跌倒重点：保持过道明亮通畅，地垫防滑固定，浴室加装扶手与防滑垫，夜间卫生间可开小夜灯。常用物品放在齐腰高度，避免踩高凳取物。', 'seed-6-0'),
(6, 1, '老人起床、如厕后宜先坐稳半分钟再站立行走。穿合脚防滑鞋，避免穿拖鞋外出。使用助行器或拐杖时，家属应定期检查胶垫是否磨损。', 'seed-6-1'),
(6, 2, '若老人曾跌倒，即使无明显外伤也建议社区医生评估；反复跌倒需排查视力、血压药物、平衡能力等问题。社区定期开展防跌倒讲座，欢迎家属陪同参加。', 'seed-6-2'),
(7, 0, '社区体检一般包括：血压、血糖、血脂、心电图、肝肾功能等基础项目。年满65周岁户籍老人每年可享受一次免费基础体检，需携带身份证提前预约。', 'seed-7-0'),
(7, 1, '体检前一晚清淡饮食，体检当日空腹，可少量饮水服药（降压药按医嘱）。体检后3—5个工作日出报告，异常指标由社区医生电话随访或预约解读。', 'seed-7-1'),
(7, 2, '报告中的「偏高」「偏低」不代表确诊，请勿自行停药或加药。如需进一步检查，社区可协助转诊至合作医院。体检当天如有发热、急性腹泻，请改约日期。', 'seed-7-2'),
(8, 0, '陪伴认知障碍（含阿尔茨海默病）老人时，宜保持环境安静熟悉，作息规律。交流时语速放慢、一次只说一件事，多用肯定与引导，少责备。', 'seed-8-0'),
(8, 1, '走失预防：出门佩戴写有姓名与联系电话的卡片或定位手环；家中门锁可加装防走失提醒。外出尽量有人陪同，熟悉固定散步路线。', 'seed-8-1'),
(8, 2, '家属压力较大时可向社区申请喘息服务或参加照护者支持小组。出现攻击行为、昼夜颠倒加重时，及时联系专科门诊，勿自行增加镇静类药物。', 'seed-8-2'),
(9, 0, '老年人感冒时可选用对症药物缓解鼻塞、咳嗽、发热，但应先阅读说明书中的「老年人用药」提示，并告知社区医生正在服用的慢病药物，避免重复含对乙酰氨基酚的复方制剂。', 'seed-9-0'),
(9, 1, '感冒期间多饮水、休息，清淡饮食。发热超过38.5℃或持续3天不退，或出现胸痛、气促、意识不清，应尽快就医，警惕肺部感染。', 'seed-9-1'),
(9, 2, '抗菌药物（抗生素）不能用于病毒性感冒，须由医生评估后使用。感冒药与降压药、降糖药同服时，注意观察血压与血糖波动，必要时咨询药师。', 'seed-9-2');

-- -----------------------------------------------------------------------------
-- 图表与演示充实数据（相对日期，保证管理端概览近 7 日饱满）
-- -----------------------------------------------------------------------------

INSERT INTO service_booking
  (elder_id, catalog_id, booking_time, status, source, remark, slot_lock, version)
VALUES
-- 六天前
(1, 1, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 6 DAY), '09:00:00'), 'done',      'manual', '体检完成', NULL, 0),
(2, 2, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 6 DAY), '10:00:00'), 'done',      'manual', '护理完成', NULL, 0),
(1, 3, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 6 DAY), '14:00:00'), 'cancelled','manual', '家政取消', NULL, 0),
-- 五天前
(2, 1, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 5 DAY), '09:30:00'), 'done',      'agent',  '体检完成', NULL, 0),
(1, 2, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 5 DAY), '11:00:00'), 'confirmed','manual', '护理确认',
 CONCAT('2:', DATE_FORMAT(TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 5 DAY), '11:00:00'), '%Y%m%d%H%i')), 0),
(2, 3, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 5 DAY), '15:00:00'), 'done',      'manual', '家政完成', NULL, 0),
(1, 1, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 5 DAY), '16:00:00'), 'cancelled','agent',  '体检取消', NULL, 0),
-- 四天前
(1, 2, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 4 DAY), '09:00:00'), 'done',      'manual', '护理完成', NULL, 0),
(2, 3, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 4 DAY), '10:30:00'), 'confirmed','manual', '家政确认',
 CONCAT('3:', DATE_FORMAT(TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 4 DAY), '10:30:00'), '%Y%m%d%H%i')), 0),
(1, 1, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 4 DAY), '14:00:00'), 'done',      'agent',  '体检完成', NULL, 0),
(2, 2, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 4 DAY), '15:30:00'), 'pending',  'manual', '护理待确认',
 CONCAT('2:', DATE_FORMAT(TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 4 DAY), '15:30:00'), '%Y%m%d%H%i')), 0),
(1, 3, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 4 DAY), '16:30:00'), 'done',      'manual', '家政完成', NULL, 0),
-- 三天前
(2, 1, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 3 DAY), '09:00:00'), 'done',      'manual', '体检完成', NULL, 0),
(1, 3, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 3 DAY), '10:00:00'), 'confirmed','agent',  '家政确认',
 CONCAT('3:', DATE_FORMAT(TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 3 DAY), '10:00:00'), '%Y%m%d%H%i')), 0),
(2, 2, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 3 DAY), '11:30:00'), 'done',      'manual', '护理完成', NULL, 0),
(1, 1, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 3 DAY), '14:30:00'), 'cancelled','manual', '体检取消', NULL, 0),
(2, 3, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 3 DAY), '16:00:00'), 'pending',  'manual', '家政待确认',
 CONCAT('3:', DATE_FORMAT(TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 3 DAY), '16:00:00'), '%Y%m%d%H%i')), 0),
-- 两天前
(1, 2, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 2 DAY), '08:30:00'), 'done',      'agent',  '护理完成', NULL, 0),
(2, 1, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 2 DAY), '09:30:00'), 'confirmed','manual', '体检确认',
 CONCAT('1:', DATE_FORMAT(TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 2 DAY), '09:30:00'), '%Y%m%d%H%i')), 0),
(1, 3, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 2 DAY), '11:00:00'), 'done',      'manual', '家政完成', NULL, 0),
(2, 2, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 2 DAY), '13:00:00'), 'pending',  'agent',  '护理待确认',
 CONCAT('2:', DATE_FORMAT(TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 2 DAY), '13:00:00'), '%Y%m%d%H%i')), 0),
(1, 1, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 2 DAY), '15:00:00'), 'done',      'manual', '体检完成', NULL, 0),
(2, 3, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 2 DAY), '16:30:00'), 'confirmed','manual', '家政确认',
 CONCAT('3:', DATE_FORMAT(TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 2 DAY), '16:30:00'), '%Y%m%d%H%i')), 0),
-- 一天前
(1, 3, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 1 DAY), '09:00:00'), 'done',      'manual', '家政完成', NULL, 0),
(2, 2, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 1 DAY), '10:00:00'), 'confirmed','agent',  '护理确认',
 CONCAT('2:', DATE_FORMAT(TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 1 DAY), '10:00:00'), '%Y%m%d%H%i')), 0),
(1, 1, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 1 DAY), '11:00:00'), 'pending',  'manual', '体检待确认',
 CONCAT('1:', DATE_FORMAT(TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 1 DAY), '11:00:00'), '%Y%m%d%H%i')), 0),
(2, 1, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 1 DAY), '14:00:00'), 'done',      'manual', '体检完成', NULL, 0),
(1, 2, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 1 DAY), '15:30:00'), 'cancelled','manual', '护理取消', NULL, 0),
(2, 3, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 1 DAY), '16:00:00'), 'confirmed','agent',  '家政确认',
 CONCAT('3:', DATE_FORMAT(TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 1 DAY), '16:00:00'), '%Y%m%d%H%i')), 0),
-- 今天
(1, 2, TIMESTAMP(CURDATE(), '09:00:00'), 'confirmed', 'manual', '护理确认',
 CONCAT('2:', DATE_FORMAT(TIMESTAMP(CURDATE(), '09:00:00'), '%Y%m%d%H%i')), 0),
(2, 3, TIMESTAMP(CURDATE(), '10:30:00'), 'pending',   'agent',  '家政待确认',
 CONCAT('3:', DATE_FORMAT(TIMESTAMP(CURDATE(), '10:30:00'), '%Y%m%d%H%i')), 0),
(1, 1, TIMESTAMP(CURDATE(), '13:00:00'), 'confirmed', 'manual', '体检确认',
 CONCAT('1:', DATE_FORMAT(TIMESTAMP(CURDATE(), '13:00:00'), '%Y%m%d%H%i')), 0),
(2, 2, TIMESTAMP(CURDATE(), '15:00:00'), 'pending',   'manual', '护理待确认',
 CONCAT('2:', DATE_FORMAT(TIMESTAMP(CURDATE(), '15:00:00'), '%Y%m%d%H%i')), 0),
(1, 3, TIMESTAMP(CURDATE(), '16:30:00'), 'cancelled', 'manual', '家政取消', NULL, 0),
-- 未来几天（待确认/已确认，充实服务类型）
(2, 1, TIMESTAMP(DATE_ADD(CURDATE(), INTERVAL 1 DAY), '09:00:00'), 'pending', 'agent', '体检待确认',
 CONCAT('1:', DATE_FORMAT(TIMESTAMP(DATE_ADD(CURDATE(), INTERVAL 1 DAY), '09:00:00'), '%Y%m%d%H%i')), 0),
(1, 2, TIMESTAMP(DATE_ADD(CURDATE(), INTERVAL 1 DAY), '14:00:00'), 'confirmed', 'manual', '护理确认',
 CONCAT('2:', DATE_FORMAT(TIMESTAMP(DATE_ADD(CURDATE(), INTERVAL 1 DAY), '14:00:00'), '%Y%m%d%H%i')), 0),
(2, 3, TIMESTAMP(DATE_ADD(CURDATE(), INTERVAL 2 DAY), '10:00:00'), 'pending', 'manual', '家政待确认',
 CONCAT('3:', DATE_FORMAT(TIMESTAMP(DATE_ADD(CURDATE(), INTERVAL 2 DAY), '10:00:00'), '%Y%m%d%H%i')), 0),
(1, 1, TIMESTAMP(DATE_ADD(CURDATE(), INTERVAL 3 DAY), '15:00:00'), 'confirmed', 'agent', '体检确认',
 CONCAT('1:', DATE_FORMAT(TIMESTAMP(DATE_ADD(CURDATE(), INTERVAL 3 DAY), '15:00:00'), '%Y%m%d%H%i')), 0);

-- ---------------------------------------------------------------------------
-- 智能助手工具调用日志：丰富饼图分布
-- ---------------------------------------------------------------------------
INSERT INTO agent_tool_call_log
  (session_id, conversation_id, user_id, tool_name, request_args, response_data, status, cost_ms, create_time)
VALUES
('a8f3c1e0-4b2d-41a9-9c0e-000000000001', NULL, 2, 'check_medication_schedule', '{"elderId":1}', '{"missed":2}', 1, 120, DATE_SUB(NOW(), INTERVAL 6 DAY) + INTERVAL 9 HOUR),
('a8f3c1e0-4b2d-41a9-9c0e-000000000001', NULL, 2, 'notify_family', '{"elderId":1}', '{"notified":1}', 1, 95, DATE_SUB(NOW(), INTERVAL 6 DAY) + INTERVAL 9 HOUR + INTERVAL 2 SECOND),
('a8f3c1e0-4b2d-41a9-9c0e-000000000002', NULL, 3, 'query_health_record', '{"elderId":2}', '{"ok":true}', 1, 88, DATE_SUB(NOW(), INTERVAL 6 DAY) + INTERVAL 11 HOUR),
('a8f3c1e0-4b2d-41a9-9c0e-000000000002', NULL, 3, 'query_knowledge_base', '{"q":"降压药"}', '{"hits":3}', 1, 210, DATE_SUB(NOW(), INTERVAL 6 DAY) + INTERVAL 11 HOUR + INTERVAL 3 SECOND),

('a8f3c1e0-4b2d-41a9-9c0e-000000000003', NULL, 2, 'query_available_service', '{"type":"nursing"}', '{"slots":4}', 1, 140, DATE_SUB(NOW(), INTERVAL 5 DAY) + INTERVAL 10 HOUR),
('a8f3c1e0-4b2d-41a9-9c0e-000000000003', NULL, 2, 'book_service', '{"catalogId":2}', '{"bookingId":0}', 1, 180, DATE_SUB(NOW(), INTERVAL 5 DAY) + INTERVAL 10 HOUR + INTERVAL 2 SECOND),
('a8f3c1e0-4b2d-41a9-9c0e-000000000003', NULL, 2, 'notify_family', '{"elderId":1}', '{"notified":1}', 1, 90, DATE_SUB(NOW(), INTERVAL 5 DAY) + INTERVAL 10 HOUR + INTERVAL 4 SECOND),
('a8f3c1e0-4b2d-41a9-9c0e-000000000004', NULL, 3, 'check_medication_schedule', '{"elderId":2}', '{"missed":0}', 1, 110, DATE_SUB(NOW(), INTERVAL 5 DAY) + INTERVAL 15 HOUR),
('a8f3c1e0-4b2d-41a9-9c0e-000000000004', NULL, 3, 'query_knowledge_base', '{"q":"糖尿病饮食"}', '{"hits":2}', 1, 195, DATE_SUB(NOW(), INTERVAL 5 DAY) + INTERVAL 15 HOUR + INTERVAL 2 SECOND),

('a8f3c1e0-4b2d-41a9-9c0e-000000000005', NULL, 2, 'check_medication_schedule', '{"elderId":1}', '{"missed":1}', 1, 105, DATE_SUB(NOW(), INTERVAL 4 DAY) + INTERVAL 9 HOUR),
('a8f3c1e0-4b2d-41a9-9c0e-000000000005', NULL, 2, 'query_available_service', '{"type":"health_check"}', '{"slots":3}', 1, 130, DATE_SUB(NOW(), INTERVAL 4 DAY) + INTERVAL 9 HOUR + INTERVAL 2 SECOND),
('a8f3c1e0-4b2d-41a9-9c0e-000000000005', NULL, 2, 'book_service', '{"catalogId":1}', '{"bookingId":0}', 1, 160, DATE_SUB(NOW(), INTERVAL 4 DAY) + INTERVAL 9 HOUR + INTERVAL 4 SECOND),
('a8f3c1e0-4b2d-41a9-9c0e-000000000006', NULL, 3, 'query_health_record', '{"elderId":2}', '{"ok":true}', 1, 75, DATE_SUB(NOW(), INTERVAL 4 DAY) + INTERVAL 14 HOUR),
('a8f3c1e0-4b2d-41a9-9c0e-000000000006', NULL, 3, 'query_available_service', '{"type":"housekeeping"}', '{"slots":2}', 1, 125, DATE_SUB(NOW(), INTERVAL 4 DAY) + INTERVAL 14 HOUR + INTERVAL 2 SECOND),
('a8f3c1e0-4b2d-41a9-9c0e-000000000006', NULL, 3, 'book_service', '{"catalogId":3}', '{"bookingId":0}', 1, 170, DATE_SUB(NOW(), INTERVAL 4 DAY) + INTERVAL 14 HOUR + INTERVAL 4 SECOND),

('a8f3c1e0-4b2d-41a9-9c0e-000000000007', NULL, 2, 'check_medication_schedule', '{"elderId":1}', '{"missed":3}', 1, 115, DATE_SUB(NOW(), INTERVAL 3 DAY) + INTERVAL 8 HOUR),
('a8f3c1e0-4b2d-41a9-9c0e-000000000007', NULL, 2, 'notify_family', '{"elderId":1}', '{"notified":1}', 1, 85, DATE_SUB(NOW(), INTERVAL 3 DAY) + INTERVAL 8 HOUR + INTERVAL 2 SECOND),
('a8f3c1e0-4b2d-41a9-9c0e-000000000008', NULL, 3, 'query_knowledge_base', '{"q":"防跌倒"}', '{"hits":2}', 1, 200, DATE_SUB(NOW(), INTERVAL 3 DAY) + INTERVAL 12 HOUR),
('a8f3c1e0-4b2d-41a9-9c0e-000000000008', NULL, 3, 'query_available_service', '{"type":"nursing"}', '{"slots":5}', 1, 135, DATE_SUB(NOW(), INTERVAL 3 DAY) + INTERVAL 12 HOUR + INTERVAL 2 SECOND),
('a8f3c1e0-4b2d-41a9-9c0e-000000000008', NULL, 3, 'book_service', '{"catalogId":2}', '{"bookingId":0}', 1, 155, DATE_SUB(NOW(), INTERVAL 3 DAY) + INTERVAL 12 HOUR + INTERVAL 4 SECOND),
('a8f3c1e0-4b2d-41a9-9c0e-000000000009', NULL, 2, 'query_health_record', '{"elderId":1}', '{"ok":true}', 1, 70, DATE_SUB(NOW(), INTERVAL 3 DAY) + INTERVAL 16 HOUR),

('a8f3c1e0-4b2d-41a9-9c0e-000000000010', NULL, 2, 'check_medication_schedule', '{"elderId":1}', '{"missed":1}', 1, 100, DATE_SUB(NOW(), INTERVAL 2 DAY) + INTERVAL 9 HOUR),
('a8f3c1e0-4b2d-41a9-9c0e-000000000010', NULL, 2, 'notify_family', '{"elderId":1}', '{"notified":1}', 1, 92, DATE_SUB(NOW(), INTERVAL 2 DAY) + INTERVAL 9 HOUR + INTERVAL 2 SECOND),
('a8f3c1e0-4b2d-41a9-9c0e-000000000011', NULL, 3, 'query_available_service', '{"type":"health_check"}', '{"slots":4}', 1, 128, DATE_SUB(NOW(), INTERVAL 2 DAY) + INTERVAL 11 HOUR),
('a8f3c1e0-4b2d-41a9-9c0e-000000000011', NULL, 3, 'book_service', '{"catalogId":1}', '{"bookingId":0}', 1, 175, DATE_SUB(NOW(), INTERVAL 2 DAY) + INTERVAL 11 HOUR + INTERVAL 2 SECOND),
('a8f3c1e0-4b2d-41a9-9c0e-000000000011', NULL, 3, 'notify_family', '{"elderId":2}', '{"notified":1}', 1, 80, DATE_SUB(NOW(), INTERVAL 2 DAY) + INTERVAL 11 HOUR + INTERVAL 4 SECOND),
('a8f3c1e0-4b2d-41a9-9c0e-000000000012', NULL, 2, 'query_knowledge_base', '{"q":"助餐"}', '{"hits":1}', 1, 188, DATE_SUB(NOW(), INTERVAL 2 DAY) + INTERVAL 15 HOUR),
('a8f3c1e0-4b2d-41a9-9c0e-000000000012', NULL, 2, 'query_health_record', '{"elderId":1}', '{"ok":true}', 1, 65, DATE_SUB(NOW(), INTERVAL 2 DAY) + INTERVAL 15 HOUR + INTERVAL 2 SECOND),

('a8f3c1e0-4b2d-41a9-9c0e-000000000013', NULL, 2, 'check_medication_schedule', '{"elderId":1}', '{"missed":2}', 1, 112, DATE_SUB(NOW(), INTERVAL 1 DAY) + INTERVAL 8 HOUR),
('a8f3c1e0-4b2d-41a9-9c0e-000000000013', NULL, 2, 'notify_family', '{"elderId":1}', '{"notified":1}', 1, 87, DATE_SUB(NOW(), INTERVAL 1 DAY) + INTERVAL 8 HOUR + INTERVAL 2 SECOND),
('a8f3c1e0-4b2d-41a9-9c0e-000000000014', NULL, 3, 'query_available_service', '{"type":"housekeeping"}', '{"slots":3}', 1, 122, DATE_SUB(NOW(), INTERVAL 1 DAY) + INTERVAL 10 HOUR),
('a8f3c1e0-4b2d-41a9-9c0e-000000000014', NULL, 3, 'book_service', '{"catalogId":3}', '{"bookingId":0}', 1, 165, DATE_SUB(NOW(), INTERVAL 1 DAY) + INTERVAL 10 HOUR + INTERVAL 2 SECOND),
('a8f3c1e0-4b2d-41a9-9c0e-000000000015', NULL, 2, 'query_knowledge_base', '{"q":"体检预约"}', '{"hits":2}', 1, 205, DATE_SUB(NOW(), INTERVAL 1 DAY) + INTERVAL 14 HOUR),
('a8f3c1e0-4b2d-41a9-9c0e-000000000015', NULL, 2, 'query_available_service', '{"type":"health_check"}', '{"slots":2}', 1, 118, DATE_SUB(NOW(), INTERVAL 1 DAY) + INTERVAL 14 HOUR + INTERVAL 2 SECOND),
('a8f3c1e0-4b2d-41a9-9c0e-000000000015', NULL, 2, 'book_service', '{"catalogId":1}', '{"bookingId":0}', 1, 158, DATE_SUB(NOW(), INTERVAL 1 DAY) + INTERVAL 14 HOUR + INTERVAL 4 SECOND),
('a8f3c1e0-4b2d-41a9-9c0e-000000000016', NULL, 3, 'trigger_emergency_alert', '{"elderId":2}', '{"alertId":0}', 1, 95, DATE_SUB(NOW(), INTERVAL 1 DAY) + INTERVAL 18 HOUR),

('a8f3c1e0-4b2d-41a9-9c0e-000000000017', NULL, 2, 'check_medication_schedule', '{"elderId":1}', '{"missed":1}', 1, 108, NOW() - INTERVAL 3 HOUR),
('a8f3c1e0-4b2d-41a9-9c0e-000000000017', NULL, 2, 'notify_family', '{"elderId":1}', '{"notified":1}', 1, 82, NOW() - INTERVAL 3 HOUR + INTERVAL 2 SECOND),
('a8f3c1e0-4b2d-41a9-9c0e-000000000018', NULL, 3, 'query_available_service', '{"type":"nursing"}', '{"slots":4}', 1, 133, NOW() - INTERVAL 2 HOUR),
('a8f3c1e0-4b2d-41a9-9c0e-000000000018', NULL, 3, 'book_service', '{"catalogId":2}', '{"bookingId":0}', 1, 162, NOW() - INTERVAL 2 HOUR + INTERVAL 2 SECOND),
('a8f3c1e0-4b2d-41a9-9c0e-000000000018', NULL, 3, 'notify_family', '{"elderId":2}', '{"notified":1}', 1, 78, NOW() - INTERVAL 2 HOUR + INTERVAL 4 SECOND),
('a8f3c1e0-4b2d-41a9-9c0e-000000000019', NULL, 2, 'query_knowledge_base', '{"q":"感冒药"}', '{"hits":2}', 1, 198, NOW() - INTERVAL 1 HOUR),
('a8f3c1e0-4b2d-41a9-9c0e-000000000019', NULL, 2, 'query_health_record', '{"elderId":1}', '{"ok":true}', 1, 72, NOW() - INTERVAL 1 HOUR + INTERVAL 2 SECOND),
('a8f3c1e0-4b2d-41a9-9c0e-000000000020', NULL, 3, 'check_medication_schedule', '{"elderId":2}', '{"missed":0}', 1, 98, NOW() - INTERVAL 30 MINUTE);

-- ---------------------------------------------------------------------------
-- 紧急告警（卡片「未关闭告警」）
-- ---------------------------------------------------------------------------
INSERT INTO emergency_alert (elder_id, location, message, status, create_time) VALUES
(1, '阳光社区 3 栋 201', '疑似跌倒求助', 'open', DATE_SUB(NOW(), INTERVAL 5 HOUR)),
(2, '阳光社区 5 栋 502', '家属代发紧急呼叫', 'handling', DATE_SUB(NOW(), INTERVAL 1 DAY));

INSERT INTO activity_registration (activity_id, elder_id, user_id, status) VALUES
(1, 1, 2, 'registered'),
(3, 2, 3, 'registered');
