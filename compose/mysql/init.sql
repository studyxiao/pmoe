-- 使用数据库 只是举例，请根据实际情况修改
-- USE pmoe;
CREATE TABLE `user` (
    `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '',
    `username` varchar(32) NOT NULL COMMENT '昵称',
    `mobile` char(16) NULL COMMENT '手机号',
    `password` varchar(255) NOT NULL COMMENT '密码',
    `role_id` bigint(20) unsigned NOT NULL DEFAULT '1' COMMENT '角色 ID: 1-普通用户, 2-撰稿者, 3-虚拟用户',
    `signature` varchar(200) NULL COMMENT '个性签名',
    `avatar` varchar(255) NULL COMMENT '头像',
    `email` varchar(255) NULL UNIQUE COMMENT '邮箱账号',
    `last_login` datetime NULL COMMENT '最后登录时间',
    `status` tinyint(1) NOT NULL DEFAULT '1' COMMENT '状态: 0-未激活, 1-正常, 2-禁言, 3-拉黑',
    `is_deleted` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否删除: 0-没有, 1-已删除',
    `gender` tinyint(1) NOT NULL DEFAULT '0' COMMENT '性别: 0-未设置, 1-女, 2-男',
    `birthday` date NULL COMMENT '生日',
    `address` varchar(32) COMMENT '地区',
    `company` varchar(32) COMMENT '公司',
    `career` varchar(32) COMMENT '职业',
    `home_url` varchar(255) COMMENT '个人主页',
    `github` varchar(255) COMMENT 'GitHub 主页',
    `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    `article_count` int(11) unsigned NOT NULL DEFAULT '0' COMMENT '发文数量',
    `like_count` int(11) unsigned NOT NULL DEFAULT '0' COMMENT '累计点赞数',
    PRIMARY KEY (`id`),
    UNIQUE KEY `username_del` (`username`, `is_deleted`),
    UNIQUE KEY `mobile_del` (`mobile`, `is_deleted`),
    UNIQUE KEY `email_del` (`email`, `is_deleted`),
    KEY (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户信息表';

CREATE TABLE `role` (
    `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '角色 ID',
    `name` varchar(32) NOT NULL COMMENT '角色名称',
    `info` varchar(255) NULL COMMENT '描述',
    `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    -- `status` tinyint(1) unsigned NOT NULL DEFAULT '1' COMMENT '状态: 1-有效, 0-无效',
    PRIMARY KEY (`id`),
    UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户角色';

-- 初始化 role 数据
INSERT INTO `role` (`name`) VALUES ('普通用户'), ('撰稿者'), ('虚拟用户');

CREATE TABLE `permission` (
    `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '主键 ID',
    `name` varchar(32) NOT NULL COMMENT '权限名称',
    `module` varchar(32) NOT NULL DEFAULT 'default' COMMENT '所属模块, 分类权限',
    `info` varchar(255) NULL COMMENT '描述',
    `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='权限表';

CREATE TABLE `role_permission` (
    `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '主键 ID',
    `role_id` bigint(20) unsigned NOT NULL COMMENT '角色 ID',
    `permission_id` bigint(20) unsigned NOT NULL COMMENT '权限 ID',
    `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `role_permission` (`role_id`, `permission_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色权限表';
