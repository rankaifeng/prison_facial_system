import React, { useState } from 'react';
import { ConfigProvider, Form, Input, message } from 'antd';
import { useNavigate } from 'react-router-dom';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { getFirstMenuPath } from '@/router/menus';
import { userLogin } from '@/api/globApi';
import cache from '@/utils/cache';
import jinghuiImg from '@/imgs/jinghui.png';
import './index.less';

const Login = () => {
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  const onFinish = async (values) => {
    setLoading(true);
    const res = await userLogin(values);
    setLoading(false);
    const { code, msg, data } = res;

    if (code === 1) {
      message.success(msg);
      const { prison_id, role_name, token, prison_name } = data || {};
      cache.setVal('token', token);
      cache.setVal('prisonId', prison_id);
      cache.setVal('roleName', role_name);
      cache.setVal('prisonName', prison_name);
      setTimeout(() => {
        navigate(getFirstMenuPath());
      }, 500);
    } else {
      message.error(msg || '登录失败');
    }
  }

  return (
    <div className="login-page">
      {/* 背景装饰 */}
      <div className="login-bg-grid"></div>
      <div className="login-bg-glow glow1"></div>
      <div className="login-bg-glow glow2"></div>
      <div className="login-bg-scan"></div>

      <div className="login-container">
        <div className="login-card">
          {/* 顶部装饰线 */}
          <div className="card-top-line"></div>

          {/* 警徽Logo */}
          <div className="login-header">
            <div className="logo-emblem">
              <img src={jinghuiImg} alt="警徽" style={{ width: 64, height: 64, borderRadius: '50%' }} />
            </div>
            <h1 className="login-title">罪犯进出AB门人脸识别系统</h1>
            <p className="login-subtitle">PRISON AB-GATE FACIAL RECOGNITION SYSTEM</p>
            <div className="title-divider">
              <span className="divider-line"></span>
              <span className="divider-diamond"></span>
              <span className="divider-line"></span>
            </div>
          </div>

          <ConfigProvider
            theme={{
              components: {
                Input: {
                  colorBgContainer: 'rgba(255, 255, 255, 0.04)',
                  colorBorder: 'rgba(255, 255, 255, 0.08)',
                  colorText: 'rgba(255, 255, 255, 0.85)',
                  colorTextPlaceholder: 'rgba(255, 255, 255, 0.25)',
                  activeBorderColor: 'rgba(212, 175, 55, 0.5)',
                  hoverBorderColor: 'rgba(212, 175, 55, 0.3)',
                  activeShadow: '0 0 0 2px rgba(212, 175, 55, 0.08)',
                },
              },
            }}
          >
          <Form
            form={form}
            onFinish={onFinish}
            layout="vertical"
            className="login-form"
          >
            <Form.Item
              name="username"
              rules={[{ required: true, message: '请输入账号' }]}
            >
              <Input
                prefix={<UserOutlined style={{ color: 'rgba(255,255,255,0.45)', fontSize: 15 }} />}
                placeholder="请输入账号"
                size="large"
                className="login-input"
                style={{ background: 'rgba(255,255,255,0.04)', borderColor: 'rgba(255,255,255,0.08)' }}
              />
            </Form.Item>

            <Form.Item
              name="password"
              rules={[{ required: true, message: '请输入密码' }]}
            >
              <Input.Password
                prefix={<LockOutlined style={{ color: 'rgba(255,255,255,0.45)', fontSize: 15 }} />}
                placeholder="请输入密码"
                size="large"
                className="login-input"
                style={{ background: 'rgba(255,255,255,0.04)', borderColor: 'rgba(255,255,255,0.08)' }}
              />
            </Form.Item>

            <Form.Item className="form-btn">
              <button
                type="submit"
                className="submit-btn"
                disabled={loading}
              >
                {loading ? (
                  <span className="btn-loading">
                    <span className="btn-spinner"></span>
                    登录中...
                  </span>
                ) : '安 全 登 录'}
              </button>
            </Form.Item>
          </Form>
          </ConfigProvider>

          <div className="login-footer">
            <span>© 2026 罪犯进出AB门人脸识别系统</span>
          </div>
        </div>

        {/* 底部标语 */}
        <div className="login-motto">
          科技赋能监管 · 智慧守护安全
        </div>
      </div>
    </div>
  );
};

export default Login;
