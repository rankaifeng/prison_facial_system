import React, { useState } from 'react';
import { Form, Input, message } from 'antd';
import { useNavigate } from 'react-router-dom';
import { UserOutlined, LockOutlined, SafetyOutlined } from '@ant-design/icons';
import { getFirstMenuPath } from '@/router/menus';
import { userLogin } from '@/api/globApi';
import logoImg from '@/imgs/logo.png';
import cache from '@/utils/cache';
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
      <div className="login-bg">
        <div className="bg-shape shape1"></div>
        <div className="bg-shape shape2"></div>
        <div className="bg-shape shape3"></div>
        <div className="bg-shape shape4"></div>
        <div className="bg-shape shape5"></div>
      </div>

      <div className="login-container">
        <div className="login-card">
          <div className="login-header">
            <div className="logo-icon">
              <img src={logoImg} alt="logo" />
            </div>
            <h1 className="login-title">监狱人脸识别系统</h1>
            <p className="login-subtitle">Prison Facial Recognition System</p>
          </div>

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
                prefix={<UserOutlined />}
                placeholder="请输入账号"
                size="large"
                className="login-input"
              />
            </Form.Item>

            <Form.Item
              name="password"
              rules={[{ required: true, message: '请输入密码' }]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="请输入密码"
                size="large"
                className="login-input"
              />
            </Form.Item>

            <Form.Item className="form-btn">
              <button
                type="submit"
                className="submit-btn"
                disabled={loading}
              >
                {loading ? '登录中...' : '登 录'}
              </button>
            </Form.Item>
          </Form>

          <div className="login-footer">
            <span>© 2025 监狱人脸识别系统</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
