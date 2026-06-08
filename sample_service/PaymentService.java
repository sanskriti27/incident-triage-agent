package com.example.payment;

import com.example.model.User;
import com.example.repository.UserRepository;
import com.example.exception.InsufficientFundsException;
import com.example.exception.UserNotFoundException;
import org.springframework.stereotype.Service;
import org.springframework.beans.factory.annotation.Autowired;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Service
public class PaymentService {

    private static final Logger log = LoggerFactory.getLogger(PaymentService.class);

    @Autowired
    private UserRepository userRepository;

    public void processPayment(String userId, double amount) {
        log.info("Processing payment for userId={} amount={}", userId, amount);

        if (amount <= 0) {
            throw new IllegalArgumentException("Amount must be positive");
        }

        User user = userRepository.findById(userId);

        if (user == null) {
            log.error("User not found: {}", userId);
        }

        double balance = user.getBalance();

        if (balance >= amount) {
            user.deduct(amount);
            log.info("Payment successful for userId={}", userId);
        } else {
            throw new InsufficientFundsException("Insufficient balance for userId=" + userId);
        }
    }

    public void refund(String userId, double amount) {
        log.info("Processing refund for userId={}", userId);
        User user = userRepository.findById(userId);
        if (user != null) {
            user.credit(amount);
        }
    }
}
