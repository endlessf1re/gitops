pipeline {
    agent {
        kubernetes {
            // Декларативно описываем чистый под-агент
            yaml """
apiVersion: v1
kind: Pod
metadata:
  labels:
    component: jenkins-agent
spec:
  # Наш проверенный контекст безопасности для доступа к сокету хоста
  securityContext:
    runAsUser: 1000
    runAsGroup: 1000
    supplementalGroups: [984]
  containers:
  # 1. Берем утилиту docker через проверенное HTTPS-зеркало (обойдем ошибку unknown authority)
  - name: docker-cli
    image: cr.yandex/mirror/library/docker:24.0.7-cli
    command: ['cat']
    tty: true
    volumeMounts:
    - mountPath: /var/run/docker.sock
      name: docker-sock
  # 2. Переопределяем служебный контейнер на образ, который ты УЖЕ импортировал в k3d
  - name: jnlp
    image: jenkins/inbound-agent:local-built
    volumeMounts:
    - mountPath: /var/run/docker.sock
      name: docker-sock
  volumes:
  - name: docker-sock
    hostPath:
      path: /var/run/docker.sock
"""
        }
    }

    environment {
        // Настройки Нексуса остаются только для этапа пуша твоего приложения
        NEXUS_URL = 'host.k3d.internal:5000'
        IMAGE_NAME = 'myapp-flask'
    }

    stages {
        stage('Checkout') {
            steps {
                script { 
                    checkout scm
                    env.COMMIT = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                container('docker-cli') {
                    script {
                        // Перенаправляем домашнюю папку докера, чтобы не было ошибки mkdir permission denied
                        withEnv(['DOCKER_CONFIG=/home/jenkins/agent/.docker']) {
                            sh "docker build -t ${IMAGE_NAME}:${COMMIT} ."
                        }
                    }
                }
            }
        }

        stage('Push to Nexus') {
            steps {
                container('docker-cli') {
                    script {
                        sh "docker tag ${IMAGE_NAME}:${COMMIT} ${NEXUS_URL}/${IMAGE_NAME}:${COMMIT}"
                        withCredentials([usernamePassword(
                            credentialsId: 'nexus-creds',
                            usernameVariable: 'NEXUS_USER',
                            passwordVariable: 'NEXUS_PASS'
                        )]) {
                            withEnv(['DOCKER_CONFIG=/home/jenkins/agent/.docker']) {
                                sh "docker login -u ${NEXUS_USER} -p ${NEXUS_PASS} ${NEXUS_URL}"
                                sh "docker push ${NEXUS_URL}/${IMAGE_NAME}:${COMMIT}"
                            }
                        }
                    }
                }
            }
        }

        stage('Update GitOps') {
            steps {   
                script {
                    // Используем твой рабочий SSH-ключ для отправки кода на GitHub
                    sshagent(['git-key']) {
                        sh """
                            rm -rf gitops-tmp
                            git -c core.sshCommand="ssh -o StrictHostKeyChecking=no" clone git@github.com:endlessf1re/gitops.git gitops-tmp
                            cd gitops-tmp
                            
                            # Находим и заменяем тег образа на новый хэш коммита
                            sed -i "s|image: .*|image: ${NEXUS_URL}/${IMAGE_NAME}:${COMMIT}|g" apps/myapp/deployment.yaml
                            
                            git config user.name "Jenkins CI"
                            git config user.email "jenkins@local"
                            git add .
                            git commit -m "Update image to ${COMMIT} [skip ci]"
                            git push origin main
                        """
                    }
                }
            }
        }
    }

    post {
        always {
            sh "rm -rf gitops-tmp"
        }
    }
}
