// sample_service/PaymentService.java
public class PaymentService {

    private UserRepository userRepository;

    public void processPayment(String userId, double amount) {  // line 47 - NPE here
        User user = userRepository.findById(userId);
        double balance = user.getBalance();  // null if user not found
        if (balance >= amount) {
            user.deduct(amount);
        }
    }

    public void refund(String userId, double amount) {
        User user = userRepository.findById(userId);
        user.credit(amount);
    }
}